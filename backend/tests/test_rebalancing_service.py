# ABOUTME: Tests for rebalancing service - allocation analysis and rebalancing recommendations
# ABOUTME: Unit and integration tests for portfolio rebalancing feature (Epic 8 - F8.7-001)

import pytest
import pytest_asyncio
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from rebalancing_service import RebalancingService
from rebalancing_models import (
    AllocationModel,
    MODERATE_MODEL,
    AGGRESSIVE_MODEL,
    CONSERVATIVE_MODEL,
    get_model,
    create_custom_model,
)
from rebalancing_schemas import AllocationStatus
from models import Transaction, Position, AssetType, TransactionType, Base


# Use SQLite for testing (in-memory database)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest_asyncio.fixture
async def db_session():
    """Create a test database session"""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Provide session
    async with TestSessionLocal() as session:
        yield session

    # Cleanup
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def sample_portfolio(db_session):
    """Create a sample portfolio with diversified positions"""
    positions = [
        # Stocks: €27,500 (55%)
        Position(
            symbol="AMEM",
            asset_type=AssetType.STOCK,
            quantity=Decimal("100"),
            avg_cost_basis=Decimal("225.00"),
            total_cost_basis=Decimal("22500.00"),
            current_price=Decimal("275.00"),
            currency="EUR",
            first_purchase_date=datetime(2024, 1, 1),
            last_transaction_date=datetime(2024, 1, 1)
        ),
        Position(
            symbol="MSTR",
            asset_type=AssetType.STOCK,
            quantity=Decimal("20"),
            avg_cost_basis=Decimal("200.00"),
            total_cost_basis=Decimal("4000.00"),
            current_price=Decimal("250.00"),
            currency="EUR",
            first_purchase_date=datetime(2024, 2, 1),
            last_transaction_date=datetime(2024, 2, 1)
        ),
        # Crypto: €17,500 (35%)
        Position(
            symbol="BTC",
            asset_type=AssetType.CRYPTO,
            quantity=Decimal("0.2"),
            avg_cost_basis=Decimal("70000.00"),
            total_cost_basis=Decimal("14000.00"),
            current_price=Decimal("80000.00"),
            currency="EUR",
            first_purchase_date=datetime(2024, 1, 15),
            last_transaction_date=datetime(2024, 1, 15)
        ),
        Position(
            symbol="ETH",
            asset_type=AssetType.CRYPTO,
            quantity=Decimal("2"),
            avg_cost_basis=Decimal("1500.00"),
            total_cost_basis=Decimal("3000.00"),
            current_price=Decimal("1750.00"),
            currency="EUR",
            first_purchase_date=datetime(2024, 1, 20),
            last_transaction_date=datetime(2024, 1, 20)
        ),
        # Metals: €5,000 (10%)
        Position(
            symbol="XAU",
            asset_type=AssetType.METAL,
            quantity=Decimal("10"),
            avg_cost_basis=Decimal("450.00"),
            total_cost_basis=Decimal("4500.00"),
            current_price=Decimal("500.00"),
            currency="EUR",
            first_purchase_date=datetime(2024, 1, 10),
            last_transaction_date=datetime(2024, 1, 10)
        ),
    ]

    for pos in positions:
        db_session.add(pos)
    await db_session.commit()

    return positions


class TestRebalancingModels:
    """Test allocation model definitions"""

    def test_moderate_model_allocations(self):
        """Test moderate model has correct allocations"""
        assert MODERATE_MODEL.get_target_percentage(AssetType.STOCK) == 60
        assert MODERATE_MODEL.get_target_percentage(AssetType.CRYPTO) == 25
        assert MODERATE_MODEL.get_target_percentage(AssetType.METAL) == 15

    def test_aggressive_model_allocations(self):
        """Test aggressive model has correct allocations"""
        assert AGGRESSIVE_MODEL.get_target_percentage(AssetType.STOCK) == 50
        assert AGGRESSIVE_MODEL.get_target_percentage(AssetType.CRYPTO) == 40
        assert AGGRESSIVE_MODEL.get_target_percentage(AssetType.METAL) == 10

    def test_conservative_model_allocations(self):
        """Test conservative model has correct allocations"""
        assert CONSERVATIVE_MODEL.get_target_percentage(AssetType.STOCK) == 70
        assert CONSERVATIVE_MODEL.get_target_percentage(AssetType.CRYPTO) == 15
        assert CONSERVATIVE_MODEL.get_target_percentage(AssetType.METAL) == 15

    def test_get_model_by_name(self):
        """Test retrieving model by name"""
        model = get_model("moderate")
        assert model.name == "moderate"
        assert model.get_target_percentage(AssetType.STOCK) == 60

    def test_get_model_invalid_name(self):
        """Test error on invalid model name"""
        with pytest.raises(ValueError, match="Unknown model"):
            get_model("invalid_model")

    def test_create_custom_model(self):
        """Test creating custom allocation model"""
        model = create_custom_model(stocks=50, crypto=30, metals=20)
        assert model.name == "custom"
        assert model.get_target_percentage(AssetType.STOCK) == 50
        assert model.get_target_percentage(AssetType.CRYPTO) == 30
        assert model.get_target_percentage(AssetType.METAL) == 20

    def test_custom_model_must_sum_to_100(self):
        """Test custom model validation - must sum to 100%"""
        with pytest.raises(ValueError, match="must sum to 100%"):
            create_custom_model(stocks=50, crypto=30, metals=30)  # Sums to 110

    def test_custom_model_invalid_percentages(self):
        """Test custom model validation - percentages must be 0-100"""
        with pytest.raises(ValueError, match="must be between 0 and 100"):
            create_custom_model(stocks=150, crypto=-10, metals=10)


class TestRebalancingService:
    """Test rebalancing service allocation analysis"""

    @pytest.mark.asyncio
    async def test_calculate_current_allocation(self, db_session, sample_portfolio):
        """Test calculating current allocation from positions"""
        service = RebalancingService(db_session)

        allocation = await service._calculate_current_allocation()

        # Total portfolio:
        # Stocks: 100 × 275 + 20 × 250 = 27,500 + 5,000 = 32,500
        # Crypto: 0.2 × 80,000 + 2 × 1,750 = 16,000 + 3,500 = 19,500
        # Metals: 10 × 500 = 5,000
        # Total: 57,000
        assert allocation[AssetType.STOCK]["value"] == Decimal("32500.00")
        assert allocation[AssetType.CRYPTO]["value"] == Decimal("19500.00")
        assert allocation[AssetType.METAL]["value"] == Decimal("5000.00")

    @pytest.mark.asyncio
    async def test_analyze_moderate_model(self, db_session, sample_portfolio):
        """Test rebalancing analysis with moderate model"""
        service = RebalancingService(db_session)

        analysis = await service.analyze_rebalancing(target_model="moderate")

        # Portfolio: Stocks 32,500 (57%), Crypto 19,500 (34%), Metals 5,000 (9%)
        # Target (Moderate): Stocks 60%, Crypto 25%, Metals 15%
        assert analysis.total_portfolio_value == Decimal("57000.00")
        assert analysis.target_model == "moderate"
        assert analysis.rebalancing_required is True

        # Check stocks (underweight -3%)
        stocks_alloc = next(a for a in analysis.current_allocation if a.asset_type == AssetType.STOCK)
        assert abs(stocks_alloc.current_percentage - Decimal("57.02")) < Decimal("0.1")  # ~57%
        assert stocks_alloc.target_percentage == Decimal("60.00")
        assert abs(stocks_alloc.deviation - Decimal("-2.98")) < Decimal("0.1")  # ~-3%
        assert stocks_alloc.status == AllocationStatus.SLIGHTLY_UNDERWEIGHT
        assert stocks_alloc.rebalancing_needed is False  # Within ±5% threshold

        # Check crypto (overweight +9%)
        crypto_alloc = next(a for a in analysis.current_allocation if a.asset_type == AssetType.CRYPTO)
        assert abs(crypto_alloc.current_percentage - Decimal("34.21")) < Decimal("0.1")  # ~34%
        assert crypto_alloc.target_percentage == Decimal("25.00")
        assert abs(crypto_alloc.deviation - Decimal("9.21")) < Decimal("0.1")  # ~+9%
        assert crypto_alloc.status == AllocationStatus.OVERWEIGHT
        assert crypto_alloc.rebalancing_needed is True

        # Check metals (underweight -6%)
        metals_alloc = next(a for a in analysis.current_allocation if a.asset_type == AssetType.METAL)
        assert abs(metals_alloc.current_percentage - Decimal("8.77")) < Decimal("0.1")  # ~9%
        assert metals_alloc.target_percentage == Decimal("15.00")
        assert abs(metals_alloc.deviation - Decimal("-6.23")) < Decimal("0.1")  # ~-6%
        assert metals_alloc.status == AllocationStatus.UNDERWEIGHT
        assert metals_alloc.rebalancing_needed is True

    @pytest.mark.asyncio
    async def test_analyze_aggressive_model(self, db_session, sample_portfolio):
        """Test rebalancing analysis with aggressive model"""
        service = RebalancingService(db_session)

        analysis = await service.analyze_rebalancing(target_model="aggressive")

        # Aggressive: Stocks 50%, Crypto 40%, Metals 10%
        # Current: Stocks 57%, Crypto 34%, Metals 9%
        assert analysis.target_model == "aggressive"

        stocks_alloc = next(a for a in analysis.current_allocation if a.asset_type == AssetType.STOCK)
        assert stocks_alloc.target_percentage == Decimal("50.00")
        assert stocks_alloc.status == AllocationStatus.OVERWEIGHT  # 57% vs 50% = +7%

    @pytest.mark.asyncio
    async def test_analyze_conservative_model(self, db_session, sample_portfolio):
        """Test rebalancing analysis with conservative model"""
        service = RebalancingService(db_session)

        analysis = await service.analyze_rebalancing(target_model="conservative")

        # Conservative: Stocks 70%, Crypto 15%, Metals 15%
        # Current: Stocks 57%, Crypto 34%, Metals 9%
        assert analysis.target_model == "conservative"

        # Stocks should be underweight (57% vs 70% = -13%)
        stocks_alloc = next(a for a in analysis.current_allocation if a.asset_type == AssetType.STOCK)
        assert abs(stocks_alloc.deviation - Decimal("-12.98")) < Decimal("0.1")  # ~-13%
        assert stocks_alloc.status == AllocationStatus.UNDERWEIGHT

    @pytest.mark.asyncio
    async def test_analyze_custom_model(self, db_session, sample_portfolio):
        """Test rebalancing analysis with custom model"""
        service = RebalancingService(db_session)

        analysis = await service.analyze_rebalancing(
            target_model="custom",
            custom_stocks=50,
            custom_crypto=30,
            custom_metals=20
        )

        assert analysis.target_model == "custom"

        stocks_alloc = next(a for a in analysis.current_allocation if a.asset_type == AssetType.STOCK)
        assert stocks_alloc.target_percentage == Decimal("50.00")

    @pytest.mark.asyncio
    async def test_balanced_portfolio_no_rebalancing(self, db_session):
        """Test that a balanced portfolio doesn't require rebalancing"""
        # Create perfectly balanced portfolio (60/25/15)
        positions = [
            Position(
                symbol="STOCK1",
                asset_type=AssetType.STOCK,
                quantity=Decimal("60"),
                current_price=Decimal("1.00"),
                avg_cost_basis=Decimal("1.00"),
                total_cost_basis=Decimal("60.00"),
                currency="EUR"
            ),
            Position(
                symbol="CRYPTO1",
                asset_type=AssetType.CRYPTO,
                quantity=Decimal("25"),
                current_price=Decimal("1.00"),
                avg_cost_basis=Decimal("1.00"),
                total_cost_basis=Decimal("25.00"),
                currency="EUR"
            ),
            Position(
                symbol="METAL1",
                asset_type=AssetType.METAL,
                quantity=Decimal("15"),
                current_price=Decimal("1.00"),
                avg_cost_basis=Decimal("1.00"),
                total_cost_basis=Decimal("15.00"),
                currency="EUR"
            ),
        ]

        for pos in positions:
            db_session.add(pos)
        await db_session.commit()

        service = RebalancingService(db_session)
        analysis = await service.analyze_rebalancing(target_model="moderate")

        # Should not require rebalancing (all within ±2% tolerance)
        assert analysis.rebalancing_required is False
        assert analysis.total_trades_needed == 0

    @pytest.mark.asyncio
    async def test_empty_portfolio_handling(self, db_session):
        """Test handling of empty portfolio"""
        service = RebalancingService(db_session)

        analysis = await service.analyze_rebalancing(target_model="moderate")

        assert analysis.total_portfolio_value == Decimal("0")
        assert analysis.rebalancing_required is False
        assert len(analysis.current_allocation) == 0

    @pytest.mark.asyncio
    async def test_single_asset_type_portfolio(self, db_session):
        """Test portfolio with only one asset type"""
        position = Position(
            symbol="BTC",
            asset_type=AssetType.CRYPTO,
            quantity=Decimal("1"),
            current_price=Decimal("50000.00"),
            avg_cost_basis=Decimal("40000.00"),
            total_cost_basis=Decimal("40000.00"),
            currency="EUR"
        )
        db_session.add(position)
        await db_session.commit()

        service = RebalancingService(db_session)
        analysis = await service.analyze_rebalancing(target_model="moderate")

        # Crypto is 100%, should be very overweight vs 25% target
        assert analysis.rebalancing_required is True

        crypto_alloc = next(a for a in analysis.current_allocation if a.asset_type == AssetType.CRYPTO)
        assert crypto_alloc.current_percentage == Decimal("100.00")
        assert crypto_alloc.deviation == Decimal("75.00")  # 100% - 25% = +75%

    @pytest.mark.asyncio
    async def test_extreme_concentration_detection(self, db_session):
        """Test detection of extreme concentration risk"""
        # Portfolio with 95% in one asset
        positions = [
            Position(
                symbol="BTC",
                asset_type=AssetType.CRYPTO,
                quantity=Decimal("1"),
                current_price=Decimal("95000.00"),
                avg_cost_basis=Decimal("80000.00"),
                total_cost_basis=Decimal("80000.00"),
                currency="EUR"
            ),
            Position(
                symbol="STOCK1",
                asset_type=AssetType.STOCK,
                quantity=Decimal("50"),
                current_price=Decimal("100.00"),
                avg_cost_basis=Decimal("100.00"),
                total_cost_basis=Decimal("5000.00"),
                currency="EUR"
            ),
        ]

        for pos in positions:
            db_session.add(pos)
        await db_session.commit()

        service = RebalancingService(db_session)
        analysis = await service.analyze_rebalancing(target_model="moderate")

        # Should identify extreme overweight
        assert analysis.most_overweight == "crypto"
        assert analysis.largest_deviation == Decimal("70.00")  # 95% - 25% = 70%

    @pytest.mark.asyncio
    async def test_determine_allocation_status(self, db_session):
        """Test allocation status determination logic"""
        service = RebalancingService(db_session)

        # Test BALANCED (within ±2%)
        assert service._determine_allocation_status(Decimal("0.0")) == AllocationStatus.BALANCED
        assert service._determine_allocation_status(Decimal("1.5")) == AllocationStatus.BALANCED
        assert service._determine_allocation_status(Decimal("-2.0")) == AllocationStatus.BALANCED

        # Test SLIGHTLY_OVERWEIGHT (2-5%)
        assert service._determine_allocation_status(Decimal("3.0")) == AllocationStatus.SLIGHTLY_OVERWEIGHT
        assert service._determine_allocation_status(Decimal("4.9")) == AllocationStatus.SLIGHTLY_OVERWEIGHT

        # Test SLIGHTLY_UNDERWEIGHT (-5% to -2%)
        assert service._determine_allocation_status(Decimal("-3.0")) == AllocationStatus.SLIGHTLY_UNDERWEIGHT
        assert service._determine_allocation_status(Decimal("-4.9")) == AllocationStatus.SLIGHTLY_UNDERWEIGHT

        # Test OVERWEIGHT (>5%)
        assert service._determine_allocation_status(Decimal("5.1")) == AllocationStatus.OVERWEIGHT
        assert service._determine_allocation_status(Decimal("15.0")) == AllocationStatus.OVERWEIGHT

        # Test UNDERWEIGHT (<-5%)
        assert service._determine_allocation_status(Decimal("-5.1")) == AllocationStatus.UNDERWEIGHT
        assert service._determine_allocation_status(Decimal("-15.0")) == AllocationStatus.UNDERWEIGHT

    @pytest.mark.asyncio
    async def test_transaction_costs_estimation(self, db_session, sample_portfolio):
        """Test estimation of transaction costs"""
        service = RebalancingService(db_session)

        analysis = await service.analyze_rebalancing(target_model="moderate")

        # Should estimate costs based on trade volume
        # With 0.5% fee rate and rebalancing needed
        assert analysis.estimated_transaction_costs > Decimal("0")

        # Rough check: costs should be < 1% of portfolio value
        max_expected_costs = analysis.total_portfolio_value * Decimal("0.01")
        assert analysis.estimated_transaction_costs < max_expected_costs
