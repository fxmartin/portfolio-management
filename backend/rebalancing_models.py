# ABOUTME: Target allocation models for portfolio rebalancing
# ABOUTME: Defines predefined allocation strategies (moderate, aggressive, conservative)

from typing import Dict
from models import AssetType


class AllocationModel:
    """Base class for target allocation models"""

    def __init__(self, name: str, allocations: Dict[AssetType, int]):
        """
        Initialize allocation model.

        Args:
            name: Model name (e.g., "moderate", "aggressive")
            allocations: Dictionary mapping AssetType to target percentage
        """
        self.name = name
        self.allocations = allocations

        # Validate allocations sum to 100%
        total = sum(allocations.values())
        if total != 100:
            raise ValueError(f"Allocations must sum to 100%, got {total}%")

    def get_target_percentage(self, asset_type: AssetType) -> int:
        """Get target percentage for an asset type"""
        return self.allocations.get(asset_type, 0)

    def get_all_allocations(self) -> Dict[AssetType, int]:
        """Get all target allocations"""
        return self.allocations.copy()

    def __repr__(self):
        allocs = ", ".join(f"{k.value}={v}%" for k, v in self.allocations.items())
        return f"<AllocationModel({self.name}: {allocs})>"


# Predefined allocation models
MODERATE_MODEL = AllocationModel(
    name="moderate",
    allocations={
        AssetType.STOCK: 60,
        AssetType.CRYPTO: 25,
        AssetType.METAL: 15,
    }
)

AGGRESSIVE_MODEL = AllocationModel(
    name="aggressive",
    allocations={
        AssetType.STOCK: 50,
        AssetType.CRYPTO: 40,
        AssetType.METAL: 10,
    }
)

CONSERVATIVE_MODEL = AllocationModel(
    name="conservative",
    allocations={
        AssetType.STOCK: 70,
        AssetType.CRYPTO: 15,
        AssetType.METAL: 15,
    }
)

# Model registry for easy lookup
ALLOCATION_MODELS = {
    "moderate": MODERATE_MODEL,
    "aggressive": AGGRESSIVE_MODEL,
    "conservative": CONSERVATIVE_MODEL,
}


def get_model(model_name: str) -> AllocationModel:
    """
    Get allocation model by name.

    Args:
        model_name: One of "moderate", "aggressive", "conservative"

    Returns:
        AllocationModel instance

    Raises:
        ValueError: If model_name is not recognized
    """
    model = ALLOCATION_MODELS.get(model_name.lower())
    if not model:
        raise ValueError(
            f"Unknown model '{model_name}'. "
            f"Valid models: {', '.join(ALLOCATION_MODELS.keys())}"
        )
    return model


def create_custom_model(
    stocks: int,
    crypto: int,
    metals: int
) -> AllocationModel:
    """
    Create a custom allocation model.

    Args:
        stocks: Target percentage for stocks (0-100)
        crypto: Target percentage for crypto (0-100)
        metals: Target percentage for metals (0-100)

    Returns:
        Custom AllocationModel instance

    Raises:
        ValueError: If percentages don't sum to 100 or are out of range
    """
    # Validate ranges
    for value, name in [(stocks, "stocks"), (crypto, "crypto"), (metals, "metals")]:
        if not 0 <= value <= 100:
            raise ValueError(f"{name} percentage must be between 0 and 100, got {value}")

    # Create model (will validate sum = 100)
    return AllocationModel(
        name="custom",
        allocations={
            AssetType.STOCK: stocks,
            AssetType.CRYPTO: crypto,
            AssetType.METAL: metals,
        }
    )


# Rebalancing thresholds
TRIGGER_THRESHOLD = 5  # ±5% deviation triggers rebalancing
TOLERANCE_BAND = 2  # ±2% tolerance zone (don't rebalance if within this)
MINIMUM_TRADE_EUR = 50  # Don't suggest trades smaller than €50
TRANSACTION_COST_RATE = 0.005  # 0.5% per trade
