# ABOUTME: Integration tests for rebalancing API endpoints
# ABOUTME: Tests /api/rebalancing/analysis and /api/rebalancing/models endpoints

import pytest
import pytest_asyncio
from decimal import Decimal
from datetime import datetime
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from main import app
from models import Position, AssetType, Base
from database import get_async_db


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
async def test_client(db_session):
    """Create test HTTP client with database override"""
    async def override_get_async_db():
        yield db_session

    app.dependency_overrides[get_async_db] = override_get_async_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_portfolio(db_session):
    """Create a sample portfolio with diversified positions"""
    positions = [
        # Stocks: €32,500 (57% of €57,000)
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
        # Crypto: €19,500 (34%)
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
        # Metals: €5,000 (9%)
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


class TestRebalancingAnalysisEndpoint:
    """Test /api/rebalancing/analysis endpoint"""

    @pytest.mark.asyncio
    async def test_analysis_endpoint_moderate_model(self, test_client, sample_portfolio):
        """Test rebalancing analysis endpoint with moderate model"""
        response = await test_client.get("/api/rebalancing/analysis?target_model=moderate")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "total_portfolio_value" in data
        assert "current_allocation" in data
        assert "target_model" in data
        assert "rebalancing_required" in data
        assert "total_trades_needed" in data
        assert "estimated_transaction_costs" in data

        # Verify portfolio total
        assert float(data["total_portfolio_value"]) == 57000.00
        assert data["target_model"] == "moderate"

        # Verify allocation data exists for all asset types
        assert len(data["current_allocation"]) == 3
        asset_types = [alloc["asset_type"] for alloc in data["current_allocation"]]
        assert "STOCK" in asset_types
        assert "CRYPTO" in asset_types
        assert "METAL" in asset_types

        # Verify crypto is overweight (34% vs 25% target)
        crypto_alloc = next(a for a in data["current_allocation"] if a["asset_type"] == "CRYPTO")
        assert float(crypto_alloc["target_percentage"]) == 25.0
        assert crypto_alloc["rebalancing_needed"] is True
        assert crypto_alloc["status"] == "OVERWEIGHT"

    @pytest.mark.asyncio
    async def test_analysis_endpoint_aggressive_model(self, test_client, sample_portfolio):
        """Test rebalancing analysis with aggressive model"""
        response = await test_client.get("/api/rebalancing/analysis?target_model=aggressive")

        assert response.status_code == 200
        data = response.json()

        assert data["target_model"] == "aggressive"

        # Aggressive: Stocks 50%, Crypto 40%, Metals 10%
        stocks_alloc = next(a for a in data["current_allocation"] if a["asset_type"] == "STOCK")
        assert float(stocks_alloc["target_percentage"]) == 50.0

        crypto_alloc = next(a for a in data["current_allocation"] if a["asset_type"] == "CRYPTO")
        assert float(crypto_alloc["target_percentage"]) == 40.0

    @pytest.mark.asyncio
    async def test_analysis_endpoint_conservative_model(self, test_client, sample_portfolio):
        """Test rebalancing analysis with conservative model"""
        response = await test_client.get("/api/rebalancing/analysis?target_model=conservative")

        assert response.status_code == 200
        data = response.json()

        assert data["target_model"] == "conservative"

        # Conservative: Stocks 70%, Crypto 15%, Metals 15%
        stocks_alloc = next(a for a in data["current_allocation"] if a["asset_type"] == "STOCK")
        assert float(stocks_alloc["target_percentage"]) == 70.0

    @pytest.mark.asyncio
    async def test_analysis_endpoint_custom_model(self, test_client, sample_portfolio):
        """Test rebalancing analysis with custom allocation model"""
        response = await test_client.get(
            "/api/rebalancing/analysis"
            "?target_model=custom"
            "&custom_stocks=50"
            "&custom_crypto=30"
            "&custom_metals=20"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["target_model"] == "custom"

        # Verify custom allocations
        stocks_alloc = next(a for a in data["current_allocation"] if a["asset_type"] == "STOCK")
        assert float(stocks_alloc["target_percentage"]) == 50.0

        crypto_alloc = next(a for a in data["current_allocation"] if a["asset_type"] == "CRYPTO")
        assert float(crypto_alloc["target_percentage"]) == 30.0

        metals_alloc = next(a for a in data["current_allocation"] if a["asset_type"] == "METAL")
        assert float(metals_alloc["target_percentage"]) == 20.0

    @pytest.mark.asyncio
    async def test_analysis_endpoint_custom_model_validation_missing_params(self, test_client):
        """Test custom model validation - missing parameters"""
        response = await test_client.get(
            "/api/rebalancing/analysis"
            "?target_model=custom"
            "&custom_stocks=50"
        )

        # Router validation catches this and returns 400
        assert response.status_code == 400
        data = response.json()
        assert "requires all allocation percentages" in data["detail"]

    @pytest.mark.asyncio
    async def test_analysis_endpoint_custom_model_validation_sum_not_100(self, test_client):
        """Test custom model validation - percentages don't sum to 100"""
        response = await test_client.get(
            "/api/rebalancing/analysis"
            "?target_model=custom"
            "&custom_stocks=50"
            "&custom_crypto=30"
            "&custom_metals=30"  # Sums to 110%
        )

        # Router validation catches this and returns 400
        assert response.status_code == 400
        data = response.json()
        assert "must sum to 100%" in data["detail"]

    @pytest.mark.asyncio
    async def test_analysis_endpoint_invalid_model_name(self, test_client):
        """Test error on invalid target model name"""
        response = await test_client.get("/api/rebalancing/analysis?target_model=invalid")

        # Router validation catches this and returns 400
        assert response.status_code == 400
        data = response.json()
        assert "Invalid target_model" in data["detail"]

    @pytest.mark.asyncio
    async def test_empty_portfolio_handling(self, test_client, db_session):
        """Test endpoint with empty portfolio"""
        response = await test_client.get("/api/rebalancing/analysis?target_model=moderate")

        assert response.status_code == 200
        data = response.json()

        assert float(data["total_portfolio_value"]) == 0.0
        assert data["rebalancing_required"] is False
        assert data["total_trades_needed"] == 0
        assert len(data["current_allocation"]) == 0

    @pytest.mark.asyncio
    async def test_single_asset_type_portfolio(self, test_client, db_session):
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

        response = await test_client.get("/api/rebalancing/analysis?target_model=moderate")

        assert response.status_code == 200
        data = response.json()

        # Crypto should be 100%, very overweight vs 25% target
        assert data["rebalancing_required"] is True
        assert data["most_overweight"] == "crypto"

        crypto_alloc = next(a for a in data["current_allocation"] if a["asset_type"] == "CRYPTO")
        assert float(crypto_alloc["current_percentage"]) == 100.0
        assert float(crypto_alloc["deviation"]) == 75.0  # 100% - 25% = +75%

    @pytest.mark.asyncio
    async def test_extreme_concentration_detection(self, test_client, db_session):
        """Test detection of extreme concentration risk via API"""
        # Portfolio with 95% crypto
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

        response = await test_client.get("/api/rebalancing/analysis?target_model=moderate")

        assert response.status_code == 200
        data = response.json()

        # Should identify extreme overweight
        assert data["most_overweight"] == "crypto"
        assert float(data["largest_deviation"]) == 70.0  # 95% - 25% = 70%


class TestModelsEndpoint:
    """Test /api/rebalancing/models endpoint"""

    @pytest.mark.asyncio
    async def test_get_available_models(self, test_client):
        """Test retrieving available allocation models"""
        response = await test_client.get("/api/rebalancing/models")

        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert "models" in data
        assert "custom" in data
        assert "thresholds" in data

        # Verify model definitions
        models = data["models"]
        assert "moderate" in models
        assert "aggressive" in models
        assert "conservative" in models

        # Verify moderate model
        moderate = models["moderate"]
        assert moderate["stocks"] == 60
        assert moderate["crypto"] == 25
        assert moderate["metals"] == 15

        # Verify aggressive model
        aggressive = models["aggressive"]
        assert aggressive["stocks"] == 50
        assert aggressive["crypto"] == 40
        assert aggressive["metals"] == 10

        # Verify conservative model
        conservative = models["conservative"]
        assert conservative["stocks"] == 70
        assert conservative["crypto"] == 15
        assert conservative["metals"] == 15

        # Verify thresholds
        thresholds = data["thresholds"]
        assert "±5% deviation triggers rebalancing" in thresholds["trigger"]
        assert "±2% tolerance band" in thresholds["tolerance"]
        assert "€50 minimum trade size" in thresholds["minimum_trade"]
