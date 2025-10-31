# ABOUTME: Service for portfolio rebalancing analysis and recommendations
# ABOUTME: Calculates allocation deviations and identifies rebalancing opportunities

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models import Position, AssetType
from rebalancing_models import (
    AllocationModel,
    get_model,
    create_custom_model,
    TRIGGER_THRESHOLD,
    TOLERANCE_BAND,
    MINIMUM_TRADE_EUR,
    TRANSACTION_COST_RATE,
)
from rebalancing_schemas import (
    RebalancingAnalysis,
    AssetTypeAllocation,
    AllocationStatus,
)


class RebalancingService:
    """
    Service for portfolio rebalancing analysis.

    Analyzes current portfolio allocation against target models and identifies
    rebalancing opportunities.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize rebalancing service.

        Args:
            session: Async database session
        """
        self.session = session

    async def analyze_rebalancing(
        self,
        target_model: str = "moderate",
        custom_stocks: Optional[int] = None,
        custom_crypto: Optional[int] = None,
        custom_metals: Optional[int] = None
    ) -> RebalancingAnalysis:
        """
        Analyze portfolio allocation against target model.

        Args:
            target_model: One of "moderate", "aggressive", "conservative", "custom"
            custom_stocks: Custom stocks percentage (required if target_model="custom")
            custom_crypto: Custom crypto percentage (required if target_model="custom")
            custom_metals: Custom metals percentage (required if target_model="custom")

        Returns:
            RebalancingAnalysis with allocation breakdown and recommendations

        Raises:
            ValueError: If custom model specified but percentages invalid
        """
        # Get target allocation model
        if target_model == "custom":
            if not all([custom_stocks is not None, custom_crypto is not None, custom_metals is not None]):
                raise ValueError("Custom model requires all allocation percentages")
            allocation_model = create_custom_model(custom_stocks, custom_crypto, custom_metals)
        else:
            allocation_model = get_model(target_model)

        # Calculate current allocation
        current_allocation = await self._calculate_current_allocation()

        # Calculate total portfolio value
        total_value = sum(alloc["value"] for alloc in current_allocation.values())

        if total_value == 0:
            # Empty portfolio - no rebalancing needed
            return RebalancingAnalysis(
                total_portfolio_value=Decimal("0"),
                current_allocation=[],
                target_model=target_model,
                rebalancing_required=False,
                total_trades_needed=0,
                estimated_transaction_costs=Decimal("0"),
                largest_deviation=Decimal("0"),
                most_overweight=None,
                most_underweight=None,
                generated_at=datetime.utcnow()
            )

        # Build allocation comparison
        allocations: List[AssetTypeAllocation] = []
        deviations: List[tuple[Decimal, AssetType]] = []

        for asset_type in [AssetType.STOCK, AssetType.CRYPTO, AssetType.METAL]:
            current_value = current_allocation.get(asset_type, {}).get("value", Decimal("0"))
            current_percentage = (current_value / total_value * 100) if total_value > 0 else Decimal("0")
            target_percentage = Decimal(str(allocation_model.get_target_percentage(asset_type)))

            deviation = current_percentage - target_percentage
            status = self._determine_allocation_status(deviation)
            rebalancing_needed = abs(deviation) >= TRIGGER_THRESHOLD

            # Calculate delta in EUR
            target_value = total_value * (target_percentage / 100)
            delta_value = target_value - current_value

            allocation = AssetTypeAllocation(
                asset_type=asset_type,
                current_value=current_value,
                current_percentage=current_percentage,
                target_percentage=target_percentage,
                deviation=deviation,
                status=status,
                rebalancing_needed=rebalancing_needed,
                delta_value=delta_value,
                delta_percentage=deviation
            )
            allocations.append(allocation)

            if rebalancing_needed:
                deviations.append((abs(deviation), asset_type))

        # Sort deviations to find largest
        deviations.sort(reverse=True)

        # Identify most overweight/underweight
        most_overweight = None
        most_underweight = None
        largest_deviation = Decimal("0")

        if deviations:
            largest_deviation = deviations[0][0]

            for alloc in allocations:
                if alloc.deviation > 0 and alloc.rebalancing_needed and most_overweight is None:
                    most_overweight = alloc.asset_type.value.lower()
                if alloc.deviation < 0 and alloc.rebalancing_needed and most_underweight is None:
                    most_underweight = alloc.asset_type.value.lower()

        # Count trades needed (buy + sell for each asset that needs rebalancing)
        trades_needed = sum(1 for alloc in allocations if alloc.rebalancing_needed and abs(alloc.delta_value) >= MINIMUM_TRADE_EUR)

        # Estimate transaction costs
        total_trade_volume = sum(abs(alloc.delta_value) for alloc in allocations if alloc.rebalancing_needed)
        estimated_costs = total_trade_volume * Decimal(str(TRANSACTION_COST_RATE))

        return RebalancingAnalysis(
            total_portfolio_value=total_value,
            current_allocation=allocations,
            target_model=target_model,
            rebalancing_required=any(alloc.rebalancing_needed for alloc in allocations),
            total_trades_needed=trades_needed,
            estimated_transaction_costs=estimated_costs,
            largest_deviation=largest_deviation,
            most_overweight=most_overweight,
            most_underweight=most_underweight,
            generated_at=datetime.utcnow()
        )

    async def _calculate_current_allocation(self) -> Dict[AssetType, Dict[str, Decimal]]:
        """
        Calculate current allocation by asset type from positions.

        Returns:
            Dictionary mapping AssetType to {"value": total_value, "quantity": total_quantity}
        """
        # Query positions grouped by asset type with sum of current values
        # Note: We need current_price from positions, but if not available we'll get from price_history
        stmt = (
            select(
                Position.asset_type,
                func.sum(Position.quantity * Position.current_price).label('total_value'),
                func.sum(Position.quantity).label('total_quantity')
            )
            .where(Position.quantity > 0)  # Only open positions
            .group_by(Position.asset_type)
        )

        result = await self.session.execute(stmt)
        rows = result.all()

        allocation = {}
        for row in rows:
            allocation[row.asset_type] = {
                "value": Decimal(str(row.total_value)) if row.total_value else Decimal("0"),
                "quantity": Decimal(str(row.total_quantity)) if row.total_quantity else Decimal("0")
            }

        return allocation

    def _determine_allocation_status(self, deviation: Decimal) -> AllocationStatus:
        """
        Determine allocation status based on deviation from target.

        Args:
            deviation: Percentage point deviation (current - target)

        Returns:
            AllocationStatus enum value
        """
        abs_dev = abs(deviation)

        if abs_dev <= TOLERANCE_BAND:
            return AllocationStatus.BALANCED
        elif abs_dev <= TRIGGER_THRESHOLD:
            # Within trigger zone but outside tolerance
            if deviation > 0:
                return AllocationStatus.SLIGHTLY_OVERWEIGHT
            else:
                return AllocationStatus.SLIGHTLY_UNDERWEIGHT
        else:
            # Beyond trigger threshold
            if deviation > 0:
                return AllocationStatus.OVERWEIGHT
            else:
                return AllocationStatus.UNDERWEIGHT

    async def get_positions_by_asset_type(self, asset_type: AssetType) -> List[Position]:
        """
        Get all positions for a specific asset type.

        Args:
            asset_type: Asset type to filter by

        Returns:
            List of Position objects
        """
        stmt = (
            select(Position)
            .where(Position.asset_type == asset_type)
            .where(Position.quantity > 0)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
