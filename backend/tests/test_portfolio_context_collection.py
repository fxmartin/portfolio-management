# ABOUTME: Unit tests for portfolio context collection in position analysis
# ABOUTME: Tests asset allocation, sector allocation, top holdings, and concentration metrics (Epic 8 F8.4-003)

import pytest
from unittest.mock import Mock, AsyncMock
from decimal import Decimal
from typing import List

from prompt_renderer import PromptDataCollector
from portfolio_service import PortfolioService
from models import Position, AssetType


@pytest.fixture
def mock_portfolio_service():
    """Create a mock portfolio service."""
    service = Mock(spec=PortfolioService)
    service.get_all_positions = AsyncMock()
    return service


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = Mock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def data_collector(mock_db_session, mock_portfolio_service):
    """Create PromptDataCollector instance with mocked dependencies."""
    return PromptDataCollector(
        db=mock_db_session,
        portfolio_service=mock_portfolio_service,
        yahoo_service=None,
        twelve_data_service=None,
        alpha_vantage_service=None,
        coingecko_service=None
    )


def create_position(symbol: str, asset_type: AssetType, value: float, sector: str = None) -> Position:
    """Helper function to create position mocks."""
    position = Mock(spec=Position)
    position.symbol = symbol
    position.asset_type = asset_type
    position.current_value = Decimal(str(value))
    position.sector = sector
    return position


@pytest.fixture
def sample_portfolio_positions() -> List[Position]:
    """
    Create a sample portfolio with:
    - Total value: €50,000
    - 14 positions across 3 asset types
    - Heavy tech concentration (75% of stocks)
    """
    positions = [
        # Crypto (€15,000 = 30%)
        create_position("BTC", AssetType.CRYPTO, 10000.0),
        create_position("ETH", AssetType.CRYPTO, 3000.0),
        create_position("SOL", AssetType.CRYPTO, 1500.0),
        create_position("LINK", AssetType.CRYPTO, 500.0),

        # Stocks - Technology (€22,500 = 45% of total, 75% of stocks)
        create_position("MSTR", AssetType.STOCK, 8000.0, "Technology"),
        create_position("NVDA", AssetType.STOCK, 5000.0, "Technology"),
        create_position("AAPL", AssetType.STOCK, 4500.0, "Technology"),
        create_position("MSFT", AssetType.STOCK, 3000.0, "Technology"),
        create_position("GOOGL", AssetType.STOCK, 2000.0, "Technology"),

        # Stocks - Finance (€6,000 = 12% of total, 20% of stocks)
        create_position("JPM", AssetType.STOCK, 3500.0, "Finance"),
        create_position("BAC", AssetType.STOCK, 2500.0, "Finance"),

        # Stocks - Consumer (€1,500 = 3% of total, 5% of stocks)
        create_position("WMT", AssetType.STOCK, 1500.0, "Consumer"),

        # Metals (€5,000 = 10%)
        create_position("XAU", AssetType.METAL, 3000.0),
        create_position("XAG", AssetType.METAL, 2000.0),
    ]
    return positions


@pytest.mark.asyncio
async def test_collect_portfolio_context_full(data_collector, sample_portfolio_positions, mock_portfolio_service):
    """Test complete portfolio context collection with all fields."""
    mock_portfolio_service.get_all_positions.return_value = sample_portfolio_positions

    context = await data_collector._collect_portfolio_context()

    assert context is not None
    assert context["total_value"] == 50000.0
    assert context["position_count"] == 14
    assert "asset_allocation" in context
    assert "sector_allocation" in context
    assert "top_10_holdings" in context
    assert "concentration_metrics" in context


@pytest.mark.asyncio
async def test_calculate_asset_allocation(data_collector, sample_portfolio_positions, mock_portfolio_service):
    """Test asset type breakdown calculation."""
    mock_portfolio_service.get_all_positions.return_value = sample_portfolio_positions

    context = await data_collector._collect_portfolio_context()
    asset_alloc = context["asset_allocation"]

    # Check CRYPTO allocation (€15,000 / €50,000 = 30%)
    assert "CRYPTO" in asset_alloc
    assert asset_alloc["CRYPTO"]["value"] == 15000.0
    assert asset_alloc["CRYPTO"]["percentage"] == 30.0
    assert asset_alloc["CRYPTO"]["count"] == 4

    # Check STOCK allocation (€30,000 / €50,000 = 60%)
    assert "STOCK" in asset_alloc
    assert asset_alloc["STOCK"]["value"] == 30000.0
    assert asset_alloc["STOCK"]["percentage"] == 60.0
    assert asset_alloc["STOCK"]["count"] == 8

    # Check METAL allocation (€5,000 / €50,000 = 10%)
    assert "METAL" in asset_alloc
    assert asset_alloc["METAL"]["value"] == 5000.0
    assert asset_alloc["METAL"]["percentage"] == 10.0
    assert asset_alloc["METAL"]["count"] == 2


@pytest.mark.asyncio
async def test_calculate_sector_allocation(data_collector, sample_portfolio_positions, mock_portfolio_service):
    """Test sector distribution calculation for stock positions."""
    mock_portfolio_service.get_all_positions.return_value = sample_portfolio_positions

    context = await data_collector._collect_portfolio_context()
    sector_alloc = context["sector_allocation"]

    # Technology: €22,500 / €30,000 = 75%
    assert "Technology" in sector_alloc
    assert sector_alloc["Technology"]["value"] == 22500.0
    assert sector_alloc["Technology"]["percentage"] == 75.0
    assert sector_alloc["Technology"]["count"] == 5

    # Finance: €6,000 / €30,000 = 20%
    assert "Finance" in sector_alloc
    assert sector_alloc["Finance"]["value"] == 6000.0
    assert sector_alloc["Finance"]["percentage"] == 20.0
    assert sector_alloc["Finance"]["count"] == 2

    # Consumer: €1,500 / €30,000 = 5%
    assert "Consumer" in sector_alloc
    assert sector_alloc["Consumer"]["value"] == 1500.0
    assert sector_alloc["Consumer"]["percentage"] == 5.0
    assert sector_alloc["Consumer"]["count"] == 1


@pytest.mark.asyncio
async def test_get_top_holdings(data_collector, sample_portfolio_positions, mock_portfolio_service):
    """Test top 10 positions by weight calculation."""
    mock_portfolio_service.get_all_positions.return_value = sample_portfolio_positions

    context = await data_collector._collect_portfolio_context()
    top_holdings = context["top_10_holdings"]

    # Should have exactly 10 holdings (or less if portfolio smaller)
    assert len(top_holdings) == 10

    # First position should be BTC (€10,000 = 20%)
    assert top_holdings[0]["symbol"] == "BTC"
    assert top_holdings[0]["value"] == 10000.0
    assert top_holdings[0]["weight"] == 20.0
    assert top_holdings[0]["asset_type"] == "CRYPTO"

    # Second position should be MSTR (€8,000 = 16%)
    assert top_holdings[1]["symbol"] == "MSTR"
    assert top_holdings[1]["value"] == 8000.0
    assert top_holdings[1]["weight"] == 16.0
    assert top_holdings[1]["asset_type"] == "STOCK"
    assert top_holdings[1]["sector"] == "Technology"

    # Third position should be NVDA (€5,000 = 10%)
    assert top_holdings[2]["symbol"] == "NVDA"
    assert top_holdings[2]["value"] == 5000.0
    assert top_holdings[2]["weight"] == 10.0


@pytest.mark.asyncio
async def test_calculate_concentration_metrics(data_collector, sample_portfolio_positions, mock_portfolio_service):
    """Test concentration risk metrics calculation."""
    mock_portfolio_service.get_all_positions.return_value = sample_portfolio_positions

    context = await data_collector._collect_portfolio_context()
    concentration = context["concentration_metrics"]

    # Top 3 positions: BTC (20%) + MSTR (16%) + NVDA (10%) = 46%
    assert concentration["top_3_weight"] == 46.0

    # Max single sector: Technology = 75% of stock portfolio
    assert concentration["single_sector_max"] == 75.0

    # Max single asset: BTC = 20% of total portfolio
    assert concentration["single_asset_max"] == 20.0


@pytest.mark.asyncio
async def test_format_portfolio_context(data_collector, sample_portfolio_positions, mock_portfolio_service):
    """Test human-readable formatting of portfolio context."""
    mock_portfolio_service.get_all_positions.return_value = sample_portfolio_positions

    context = await data_collector._collect_portfolio_context()
    formatted = data_collector._format_portfolio_context(context)

    # Should be a string
    assert isinstance(formatted, str)

    # Should contain key information
    assert "€50,000" in formatted or "50000" in formatted
    assert "15 positions" in formatted or "15" in formatted
    assert "Technology" in formatted
    assert "BTC" in formatted


@pytest.mark.asyncio
async def test_portfolio_context_with_empty_portfolio(data_collector, mock_portfolio_service):
    """Test portfolio context with no positions (edge case)."""
    mock_portfolio_service.get_all_positions.return_value = []

    context = await data_collector._collect_portfolio_context()

    assert context["total_value"] == 0.0
    assert context["position_count"] == 0
    assert context["asset_allocation"] == {}
    assert context["sector_allocation"] == {}
    assert context["top_10_holdings"] == []
    assert context["concentration_metrics"]["top_3_weight"] == 0.0


@pytest.mark.asyncio
async def test_portfolio_context_with_single_position(data_collector, mock_portfolio_service):
    """Test portfolio context with only one position (edge case)."""
    single_position = [create_position("BTC", AssetType.CRYPTO, 10000.0)]
    mock_portfolio_service.get_all_positions.return_value = single_position

    context = await data_collector._collect_portfolio_context()

    assert context["total_value"] == 10000.0
    assert context["position_count"] == 1
    assert context["concentration_metrics"]["single_asset_max"] == 100.0
    assert len(context["top_10_holdings"]) == 1


@pytest.mark.asyncio
async def test_portfolio_context_with_no_stocks(data_collector, mock_portfolio_service):
    """Test portfolio context with only crypto (no sector allocation)."""
    crypto_only = [
        create_position("BTC", AssetType.CRYPTO, 5000.0),
        create_position("ETH", AssetType.CRYPTO, 3000.0),
    ]
    mock_portfolio_service.get_all_positions.return_value = crypto_only

    context = await data_collector._collect_portfolio_context()

    # Sector allocation should be empty (no stocks)
    assert context["sector_allocation"] == {}

    # Asset allocation should only have CRYPTO
    assert "CRYPTO" in context["asset_allocation"]
    assert "STOCK" not in context["asset_allocation"]


@pytest.mark.asyncio
async def test_portfolio_context_with_all_same_sector(data_collector, mock_portfolio_service):
    """Test portfolio context with 100% sector concentration."""
    all_tech = [
        create_position("AAPL", AssetType.STOCK, 3000.0, "Technology"),
        create_position("MSFT", AssetType.STOCK, 2000.0, "Technology"),
        create_position("GOOGL", AssetType.STOCK, 1000.0, "Technology"),
    ]
    mock_portfolio_service.get_all_positions.return_value = all_tech

    context = await data_collector._collect_portfolio_context()

    # Should show 100% concentration in Technology
    assert context["sector_allocation"]["Technology"]["percentage"] == 100.0
    assert context["concentration_metrics"]["single_sector_max"] == 100.0


@pytest.mark.asyncio
async def test_position_relative_rank(data_collector, sample_portfolio_positions, mock_portfolio_service):
    """Test position ranking logic (e.g., '3rd largest position')."""
    mock_portfolio_service.get_all_positions.return_value = sample_portfolio_positions

    # Test for NVDA (3rd largest: BTC=10k, MSTR=8k, NVDA=5k, 10% of portfolio)
    rank_info = await data_collector._get_position_rank("NVDA")

    assert rank_info["rank"] == 3  # 3rd largest
    assert rank_info["total_positions"] == 14
    assert rank_info["weight"] == 10.0
    assert "3rd largest position" in rank_info["description"]


@pytest.mark.asyncio
async def test_portfolio_context_zero_values(data_collector, mock_portfolio_service):
    """Test handling of positions with zero or None values."""
    positions_with_zeros = [
        create_position("BTC", AssetType.CRYPTO, 5000.0),
        create_position("ETH", AssetType.CRYPTO, 0.0),  # Zero value
    ]
    # Set one position's current_value to None
    positions_with_zeros[1].current_value = None

    mock_portfolio_service.get_all_positions.return_value = positions_with_zeros

    context = await data_collector._collect_portfolio_context()

    # Should handle gracefully and only count BTC
    assert context["total_value"] == 5000.0
    assert context["position_count"] == 2  # Both positions count in total
    assert len(context["top_10_holdings"]) == 1  # Only BTC in top holdings


@pytest.mark.asyncio
async def test_portfolio_context_currency_consistency(data_collector, sample_portfolio_positions, mock_portfolio_service):
    """Test that all monetary values are in EUR."""
    mock_portfolio_service.get_all_positions.return_value = sample_portfolio_positions

    context = await data_collector._collect_portfolio_context()

    # All values should be numeric floats (EUR)
    assert isinstance(context["total_value"], float)
    for asset_type, data in context["asset_allocation"].items():
        assert isinstance(data["value"], float)
    for sector, data in context["sector_allocation"].items():
        assert isinstance(data["value"], float)
    for holding in context["top_10_holdings"]:
        assert isinstance(holding["value"], float)


@pytest.mark.asyncio
async def test_collect_position_data_includes_portfolio_context(data_collector, sample_portfolio_positions, mock_portfolio_service):
    """Test that collect_position_data() includes full portfolio context."""
    from datetime import datetime, timedelta

    mock_portfolio_service.get_all_positions.return_value = sample_portfolio_positions

    # Mock get_position to return NVDA
    nvda_position = create_position("NVDA", AssetType.STOCK, 5000.0, "Technology")
    nvda_position.symbol = "NVDA"
    nvda_position.asset_name = "NVIDIA Corporation"
    nvda_position.quantity = Decimal("10.0")
    nvda_position.avg_cost_basis = Decimal("400.00")
    nvda_position.total_cost_basis = Decimal("4000.00")
    nvda_position.current_price = Decimal("500.00")
    nvda_position.unrealized_pnl = Decimal("1000.00")
    nvda_position.unrealized_pnl_percent = Decimal("25.00")

    mock_portfolio_service.get_position.return_value = nvda_position

    # Mock database queries for transaction context
    # Need to mock 3 queries: transaction_count, first_purchase_date (direct), first_purchase_date (for holding_period)
    first_purchase_date = datetime.utcnow() - timedelta(days=365)

    mock_results = []
    # First call: transaction count
    mock_result_1 = Mock()
    mock_result_1.scalar.return_value = 5
    mock_results.append(mock_result_1)

    # Second call: first purchase date (direct)
    mock_result_2 = Mock()
    mock_result_2.scalar.return_value = first_purchase_date
    mock_results.append(mock_result_2)

    # Third call: first purchase date (for holding period)
    mock_result_3 = Mock()
    mock_result_3.scalar.return_value = first_purchase_date
    mock_results.append(mock_result_3)

    data_collector.db.execute.side_effect = mock_results

    position_data = await data_collector.collect_position_data("NVDA")

    # Should include portfolio_context key as formatted string
    assert "portfolio_context" in position_data
    assert isinstance(position_data["portfolio_context"], str)
    # Check that it contains portfolio information
    assert "€50,000.00" in position_data["portfolio_context"]
    assert "14" in position_data["portfolio_context"]
    assert "Asset Allocation" in position_data["portfolio_context"]
