# ABOUTME: Unit tests for PromptRenderer and PromptDataCollector
# ABOUTME: Tests template rendering, type formatters, and data collection

import pytest
from decimal import Decimal
from prompt_renderer import PromptRenderer, PromptDataCollector
from models import AssetType


class TestPromptRenderer:
    """Test suite for PromptRenderer template rendering engine."""

    @pytest.fixture
    def renderer(self):
        """Create a PromptRenderer instance."""
        return PromptRenderer()

    def test_render_simple_template(self, renderer):
        """Test rendering a simple template with string variable."""
        template = "Hello {name}!"
        template_vars = {"name": "string"}
        data = {"name": "FX"}

        result = renderer.render(template, template_vars, data)
        assert result == "Hello FX!"

    def test_render_template_with_dict_format_variables(self, renderer):
        """Test rendering template with new dict-based template_variables format (with type and description)."""
        template = "Portfolio value: €{value}, Position count: {count}"
        template_vars = {
            "value": {"type": "decimal", "description": "Total portfolio value in EUR"},
            "count": {"type": "integer", "description": "Number of positions"}
        }
        data = {"value": 15000.50, "count": 10}

        result = renderer.render(template, template_vars, data)
        assert result == "Portfolio value: €15000.50, Position count: 10"

    def test_render_template_with_mixed_format_variables(self, renderer):
        """Test rendering template with mixed old (string) and new (dict) format."""
        template = "Value: €{value}, Name: {name}"
        template_vars = {
            "value": {"type": "decimal", "description": "Portfolio value"},  # New format
            "name": "string"  # Old format
        }
        data = {"value": 5000.75, "name": "Test Portfolio"}

        result = renderer.render(template, template_vars, data)
        assert result == "Value: €5000.75, Name: Test Portfolio"

    def test_render_multiple_variables(self, renderer):
        """Test rendering template with multiple variables of different types."""
        template = "Portfolio: {name}, Value: ${value}, Positions: {count}"
        template_vars = {
            "name": "string",
            "value": "decimal",
            "count": "integer"
        }
        data = {
            "name": "Growth Portfolio",
            "value": Decimal("50000.50"),
            "count": 15
        }

        result = renderer.render(template, template_vars, data)
        assert result == "Portfolio: Growth Portfolio, Value: $50000.50, Positions: 15"

    def test_render_missing_variable_raises_error(self, renderer):
        """Test that missing required variables raise ValueError."""
        template = "Value: {value}"
        template_vars = {"value": "decimal"}
        data = {}  # Missing 'value'

        with pytest.raises(ValueError, match="Missing template variables"):
            renderer.render(template, template_vars, data)

    def test_render_unknown_type_raises_error(self, renderer):
        """Test that unknown type raises ValueError."""
        template = "Value: {value}"
        template_vars = {"value": "unknown_type"}
        data = {"value": 123}

        with pytest.raises(ValueError, match="Unknown type: unknown_type"):
            renderer.render(template, template_vars, data)

    def test_render_type_conversion_error(self, renderer):
        """Test that type conversion errors are properly reported."""
        template = "Count: {count}"
        template_vars = {"count": "integer"}
        data = {"count": "not_a_number"}

        with pytest.raises(TypeError, match="Cannot format count as integer"):
            renderer.render(template, template_vars, data)


class TestDecimalFormatter:
    """Test suite for decimal formatting."""

    @pytest.fixture
    def renderer(self):
        return PromptRenderer()

    def test_format_decimal_from_int(self, renderer):
        """Test formatting integer as decimal."""
        result = renderer._format_decimal(100)
        assert result == "100.00"

    def test_format_decimal_from_float(self, renderer):
        """Test formatting float as decimal."""
        result = renderer._format_decimal(123.456)
        assert result == "123.46"  # Rounds to 2 decimal places

    def test_format_decimal_from_decimal(self, renderer):
        """Test formatting Decimal object."""
        result = renderer._format_decimal(Decimal("50000.50"))
        assert result == "50000.50"

    def test_format_decimal_none(self, renderer):
        """Test formatting None returns 0.00."""
        result = renderer._format_decimal(None)
        assert result == "0.00"

    def test_format_decimal_string_raises_error(self, renderer):
        """Test that string cannot be formatted as decimal."""
        with pytest.raises(TypeError, match="Cannot format str as decimal"):
            renderer._format_decimal("not_a_number")


class TestIntegerFormatter:
    """Test suite for integer formatting."""

    @pytest.fixture
    def renderer(self):
        return PromptRenderer()

    def test_format_integer_from_int(self, renderer):
        """Test formatting integer."""
        result = renderer._format_integer(42)
        assert result == "42"

    def test_format_integer_from_float(self, renderer):
        """Test formatting float as integer (truncates decimals)."""
        result = renderer._format_integer(42.9)
        assert result == "42"

    def test_format_integer_none(self, renderer):
        """Test formatting None returns 0."""
        result = renderer._format_integer(None)
        assert result == "0"

    def test_format_integer_from_string_number(self, renderer):
        """Test formatting numeric string as integer."""
        result = renderer._format_integer("123")
        assert result == "123"


class TestArrayFormatter:
    """Test suite for array formatting."""

    @pytest.fixture
    def renderer(self):
        return PromptRenderer()

    def test_format_empty_array(self, renderer):
        """Test formatting empty array returns 'None'."""
        result = renderer._format_array([])
        assert result == "None"

    def test_format_short_array(self, renderer):
        """Test formatting array with ≤5 items (comma-separated)."""
        result = renderer._format_array(["AAPL", "TSLA", "BTC"])
        assert result == "AAPL, TSLA, BTC"

    def test_format_long_array(self, renderer):
        """Test formatting array with >5 items (truncated with count)."""
        symbols = ["AAPL", "TSLA", "BTC", "ETH", "SOL", "AVAX", "MATIC"]
        result = renderer._format_array(symbols)
        assert result == "AAPL, TSLA, BTC, ETH, SOL (and 2 more)"

    def test_format_array_with_numbers(self, renderer):
        """Test formatting array of numbers."""
        result = renderer._format_array([10, 20, 30])
        assert result == "10, 20, 30"

    def test_format_array_mixed_types(self, renderer):
        """Test formatting array with mixed types."""
        result = renderer._format_array(["BTC", 50000, True])
        assert result == "BTC, 50000, True"


class TestObjectFormatter:
    """Test suite for object (dict) formatting."""

    @pytest.fixture
    def renderer(self):
        return PromptRenderer()

    def test_format_empty_object(self, renderer):
        """Test formatting empty dict returns 'None'."""
        result = renderer._format_object({})
        assert result == "None"

    def test_format_simple_object(self, renderer):
        """Test formatting dict with key-value pairs."""
        obj = {"stocks": 10000, "crypto": 5000, "metals": 2000}
        result = renderer._format_object(obj)
        expected = "stocks: 10000\ncrypto: 5000\nmetals: 2000"
        assert result == expected

    def test_format_object_single_item(self, renderer):
        """Test formatting dict with single item."""
        result = renderer._format_object({"total": 50000})
        assert result == "total: 50000"

    def test_format_object_with_string_values(self, renderer):
        """Test formatting dict with string values."""
        obj = {"name": "Portfolio", "status": "active"}
        result = renderer._format_object(obj)
        expected = "name: Portfolio\nstatus: active"
        assert result == expected


class TestBooleanFormatter:
    """Test suite for boolean formatting."""

    @pytest.fixture
    def renderer(self):
        return PromptRenderer()

    def test_format_boolean_true(self, renderer):
        """Test formatting True."""
        template = "Active: {active}"
        template_vars = {"active": "boolean"}
        data = {"active": True}

        result = renderer.render(template, template_vars, data)
        assert result == "Active: True"

    def test_format_boolean_false(self, renderer):
        """Test formatting False."""
        template = "Active: {active}"
        template_vars = {"active": "boolean"}
        data = {"active": False}

        result = renderer.render(template, template_vars, data)
        assert result == "Active: False"


class TestIntegrationScenarios:
    """Integration tests with realistic portfolio prompt scenarios."""

    @pytest.fixture
    def renderer(self):
        return PromptRenderer()

    def test_global_analysis_prompt(self, renderer):
        """Test rendering a complete global market analysis prompt."""
        template = """Portfolio Value: ${portfolio_value}
Position Count: {position_count}
Top Holdings: {top_holdings}
Asset Allocation:
{asset_allocation}"""

        template_vars = {
            "portfolio_value": "decimal",
            "position_count": "integer",
            "top_holdings": "array",
            "asset_allocation": "object"
        }

        data = {
            "portfolio_value": Decimal("50000.50"),
            "position_count": 15,
            "top_holdings": ["AAPL", "TSLA", "BTC", "ETH"],
            "asset_allocation": {
                "stocks": 30000,
                "crypto": 15000,
                "metals": 5000
            }
        }

        result = renderer.render(template, template_vars, data)

        assert "Portfolio Value: $50000.50" in result
        assert "Position Count: 15" in result
        assert "AAPL, TSLA, BTC, ETH" in result
        assert "stocks: 30000" in result
        assert "crypto: 15000" in result
        assert "metals: 5000" in result

    def test_position_analysis_prompt(self, renderer):
        """Test rendering a position-specific analysis prompt."""
        template = """Asset: {symbol}
Quantity: {quantity}
Current Price: ${current_price}
Unrealized P&L: ${unrealized_pnl} ({pnl_percentage}%)"""

        template_vars = {
            "symbol": "string",
            "quantity": "decimal",
            "current_price": "decimal",
            "unrealized_pnl": "decimal",
            "pnl_percentage": "decimal"
        }

        data = {
            "symbol": "BTC",
            "quantity": Decimal("0.5"),
            "current_price": Decimal("50000.00"),
            "unrealized_pnl": Decimal("5000.00"),
            "pnl_percentage": Decimal("25.00")
        }

        result = renderer.render(template, template_vars, data)

        assert "Asset: BTC" in result
        assert "Quantity: 0.50" in result
        assert "Current Price: $50000.00" in result
        assert "Unrealized P&L: $5000.00 (25.00%)" in result

    def test_extra_variables_in_template_ignored(self, renderer):
        """Test that extra variables in data (not in template) are ignored."""
        template = "Value: {value}"
        template_vars = {"value": "decimal"}
        data = {
            "value": Decimal("123.45"),
            "extra_var": "ignored"  # This extra variable should be ignored
        }

        result = renderer.render(template, template_vars, data)
        assert result == "Value: 123.45"


class TestPromptDataCollector:
    """Test suite for PromptDataCollector."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        from datetime import datetime

        class MockDB:
            def __init__(self):
                self.call_count = 0

            async def execute(self, query):
                self.call_count += 1
                call_num = self.call_count

                class MockResult:
                    def scalar(self):
                        # First call: transaction count (int)
                        if call_num == 1:
                            return 5
                        # Second call: first purchase date (datetime)
                        elif call_num == 2:
                            return datetime(2024, 1, 1)
                        return None

                    def scalar_one_or_none(self):
                        return datetime(2024, 1, 1)

                return MockResult()

        return MockDB()

    @pytest.fixture
    def mock_portfolio_service(self):
        """Mock portfolio service."""
        class MockPortfolioService:
            async def get_open_positions_summary(self, db):
                class Summary:
                    total_value = Decimal("50000.00")
                    stocks_value = Decimal("30000.00")
                    crypto_value = Decimal("15000.00")
                    metals_value = Decimal("5000.00")
                return Summary()

            async def get_all_positions(self, db=None):
                class Position:
                    def __init__(self, symbol, value, asset_type="STOCK", sector=None):
                        self.symbol = symbol
                        self.current_value = value
                        self.asset_type = asset_type
                        self.sector = sector
                        self.quantity = Decimal("1.0")
                        self.unrealized_pnl = Decimal("0")
                        self.unrealized_pnl_percentage = Decimal("0")
                        self.unrealized_pnl_percent = Decimal("0")  # Used by prompt_renderer
                        self.portfolio_percentage = Decimal("0")
                return [
                    Position("AAPL", 20000, "STOCK", "Technology"),
                    Position("TSLA", 10000, "STOCK", "Automotive"),
                    Position("BTC", 15000, "CRYPTO", None),
                    Position("GOLD", 5000, "METAL", None),
                ]

            async def get_position(self, symbol):
                class Position:
                    def __init__(self):
                        self.symbol = symbol
                        self.asset_name = symbol
                        self.quantity = Decimal("1.5")
                        self.current_price = Decimal("50000.00")
                        self.current_value = Decimal("75000.00")  # 1.5 * 50000
                        self.total_cost_basis = Decimal("60000.00")
                        self.avg_cost_basis = Decimal("40000.00")  # 60000 / 1.5
                        self.unrealized_pnl = Decimal("15000.00")
                        self.unrealized_pnl_percentage = Decimal("25.00")
                        self.unrealized_pnl_percent = Decimal("25.00")
                        self.asset_type = AssetType.CRYPTO

                if symbol == "BTC":
                    return Position()
                return None

            async def get_portfolio_pnl_summary(self):
                """Return mock P&L summary."""
                return {
                    "total_current_value": 50000.00,
                    "total_cost_basis": 45000.00,
                    "total_unrealized_pnl": 5000.00,
                    "total_realized_pnl": 2000.00,
                    "total_fees": 200.00,
                    "net_realized_pnl": 1800.00,
                    "total_pnl": 7000.00,
                    "net_total_pnl": 6800.00,
                }

            async def get_realized_pnl(self, symbol):
                """Return mock realized P&L for a symbol."""
                return {
                    "total_realized_pnl": Decimal("0"),
                    "total_fees": Decimal("0"),
                }

        return MockPortfolioService()

    @pytest.fixture
    def collector(self, mock_db, mock_portfolio_service):
        """Create PromptDataCollector instance."""
        return PromptDataCollector(mock_db, mock_portfolio_service)

    @pytest.mark.asyncio
    async def test_collect_global_data(self, collector):
        """Test collecting global portfolio data."""
        data = await collector.collect_global_data()

        # Portfolio value is sum of all positions
        assert data["portfolio_value"] == 50000.0

        # asset_allocation field contains sector allocation (stocks only)
        # Technology: 20000 (66.67% of 30000 total stocks)
        # Automotive: 10000 (33.33% of 30000 total stocks)
        assert "Technology" in data["asset_allocation"]
        assert data["asset_allocation"]["Technology"]["value"] == 20000.0
        assert "Automotive" in data["asset_allocation"]
        assert data["asset_allocation"]["Automotive"]["value"] == 10000.0

        # We now have 4 positions (AAPL, TSLA, BTC, GOLD)
        assert data["position_count"] == 4

        # top_holdings is a formatted string, not a list
        assert isinstance(data["top_holdings"], str)
        assert "AAPL" in data["top_holdings"]

    @pytest.mark.asyncio
    async def test_collect_position_data(self, collector):
        """Test collecting position-specific data."""
        data = await collector.collect_position_data("BTC")

        # Check basic position data
        assert data["symbol"] == "BTC"
        assert data["quantity"] == Decimal("1.5")
        assert data["current_price"] == Decimal("50000.00")
        assert data["cost_basis"] == Decimal("60000.00")
        assert data["unrealized_pnl"] == Decimal("15000.00")

        # asset_type in response data
        assert "asset_type" in data

        # Enhanced data fields should exist
        assert "transaction_count" in data
        assert "holding_period_days" in data

    @pytest.mark.asyncio
    async def test_collect_position_data_not_found(self, collector):
        """Test collecting data for non-existent position raises error."""
        with pytest.raises(ValueError, match="Position not found: INVALID"):
            await collector.collect_position_data("INVALID")

    @pytest.mark.asyncio
    async def test_collect_forecast_data(self, collector):
        """Test collecting forecast data."""
        data = await collector.collect_forecast_data("BTC")

        assert data["symbol"] == "BTC"
        assert data["current_price"] == Decimal("50000.00")
        assert "asset_type" in data
        assert "market_context" in data


class TestEnhancedDataCollection:
    """Test suite for enhanced data collection methods (F8.3-002)."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        from datetime import datetime

        class MockDB:
            def __init__(self):
                self.call_count = 0

            async def execute(self, query):
                self.call_count += 1
                call_num = self.call_count

                class MockResult:
                    def scalar(self):
                        # First call: transaction count (int)
                        if call_num == 1:
                            return 5
                        # Second call: first purchase date (datetime)
                        elif call_num == 2:
                            return datetime(2024, 1, 1)
                        return None

                    def scalar_one_or_none(self):
                        return datetime(2024, 1, 1)

                return MockResult()

        return MockDB()

    @pytest.fixture
    def mock_portfolio_service(self):
        """Mock portfolio service with enhanced summary."""
        class MockPortfolioService:
            async def get_open_positions_summary(self, db):
                class Summary:
                    total_value = Decimal("50000.00")
                    stocks_value = Decimal("30000.00")
                    stocks_percentage = Decimal("60.00")
                    crypto_value = Decimal("15000.00")
                    crypto_percentage = Decimal("30.00")
                    metals_value = Decimal("5000.00")
                    metals_percentage = Decimal("10.00")
                    total_unrealized_pnl = Decimal("5000.00")
                    total_unrealized_pnl_percentage = Decimal("11.11")
                return Summary()

            async def get_all_positions(self, db=None):
                class Position:
                    def __init__(self, symbol, value, pct, pnl_pct, asset_type, sector=None):
                        self.symbol = symbol
                        self.current_value = Decimal(str(value))
                        self.portfolio_percentage = Decimal(str(pct))
                        self.unrealized_pnl_percentage = Decimal(str(pnl_pct))
                        self.unrealized_pnl_percent = Decimal(str(pnl_pct))  # Used by prompt_renderer
                        self.asset_type = asset_type
                        self.sector = sector
                        self.quantity = Decimal("1.0")
                        self.unrealized_pnl = Decimal("0")

                return [
                    Position("AAPL", 20000, 40.0, 15.5, "STOCK", "Technology"),
                    Position("TSLA", 10000, 20.0, -5.2, "STOCK", "Automotive"),
                    Position("BTC", 15000, 30.0, 25.8, "CRYPTO", None),
                    Position("GOLD", 5000, 10.0, 8.3, "METAL", None),
                ]

            async def get_portfolio_pnl_summary(self):
                """Return mock P&L summary."""
                return {
                    "total_current_value": 50000.00,
                    "total_cost_basis": 45000.00,
                    "total_unrealized_pnl": 5000.00,
                    "total_realized_pnl": 2000.00,
                    "total_fees": 200.00,
                    "net_realized_pnl": 1800.00,
                    "total_pnl": 7000.00,
                    "net_total_pnl": 6800.00,
                }

            async def get_realized_pnl(self, symbol):
                """Return mock realized P&L for a symbol."""
                return {
                    "total_realized_pnl": Decimal("0"),
                    "total_fees": Decimal("0"),
                }

        return MockPortfolioService()

    @pytest.fixture
    def mock_yahoo_service(self):
        """Mock Yahoo Finance service for market indices."""
        class MockYahooService:
            async def get_quote(self, symbol):
                class QuoteData:
                    def __init__(self, price, change):
                        self.current_price = price
                        self.day_change_percent = change

                indices_data = {
                    '^GSPC': QuoteData(4500.50, 0.75),
                    '^DJI': QuoteData(35000.25, -0.25),
                    '^IXIC': QuoteData(15000.00, 1.2),
                    '^STOXX50E': QuoteData(4200.00, 0.5),
                    '^GDAXI': QuoteData(16000.00, -0.3),
                    '^VIX': QuoteData(15.00, -2.0),
                    '^TNX': QuoteData(4.5, 0.1),
                    'DX-Y.NYB': QuoteData(103.50, 0.2),
                    'GC=F': QuoteData(2000.00, -0.5),
                    'CL=F': QuoteData(75.00, 1.5),
                    'HG=F': QuoteData(4.00, 0.8),
                    'BTC-USD': QuoteData(50000.00, 2.5)
                }
                return indices_data.get(symbol)

        return MockYahooService()

    @pytest.fixture
    def collector_with_yahoo(self, mock_db, mock_portfolio_service, mock_yahoo_service):
        """Create PromptDataCollector with Yahoo Finance service."""
        return PromptDataCollector(mock_db, mock_portfolio_service, mock_yahoo_service)

    @pytest.fixture
    def collector_without_yahoo(self, mock_db, mock_portfolio_service):
        """Create PromptDataCollector without Yahoo Finance service."""
        return PromptDataCollector(mock_db, mock_portfolio_service, None)

    @pytest.mark.asyncio
    async def test_enhanced_collect_global_data_with_indices(self, collector_with_yahoo):
        """Test enhanced global data collection with market indices."""
        data = await collector_with_yahoo.collect_global_data()

        # Validate basic portfolio data
        assert data["portfolio_value"] == 50000.00
        assert data["position_count"] == 4

        # asset_allocation contains sector allocation (stocks only)
        # Technology: 20000 (66.67% of 30000 total stocks)
        # Automotive: 10000 (33.33% of 30000 total stocks)
        assert "Technology" in data["asset_allocation"]
        assert data["asset_allocation"]["Technology"]["value"] == 20000.0
        assert data["asset_allocation"]["Technology"]["percentage"] == 66.67
        assert "Automotive" in data["asset_allocation"]
        assert data["asset_allocation"]["Automotive"]["value"] == 10000.0
        assert data["asset_allocation"]["Automotive"]["percentage"] == 33.33

        # Validate performance metrics
        assert data["total_unrealized_pnl"] == 5000.00
        assert "performance" in data
        assert data["performance"]["current_pnl"] == 5000.00

        # Validate market indices
        assert "market_indices" in data
        assert "^GSPC" in data["market_indices"]
        assert data["market_indices"]["^GSPC"]["price"] == 4500.50
        assert data["market_indices"]["^GSPC"]["change"] == 0.75

        # Validate top holdings formatting (it's a string now)
        assert isinstance(data["top_holdings"], str)
        assert "AAPL" in data["top_holdings"]

    @pytest.mark.asyncio
    async def test_enhanced_collect_global_data_without_indices(self, collector_without_yahoo):
        """Test enhanced global data collection without Yahoo Finance service."""
        data = await collector_without_yahoo.collect_global_data()

        # Should still have all fields except indices
        assert data["portfolio_value"] == 50000.00
        assert "asset_allocation" in data  # Contains sector allocation for stocks
        assert "performance" in data
        assert "top_holdings" in data

        # Market indices should be empty dict when yahoo service not available
        assert data["market_indices"] == {}

    def test_calculate_sector_allocation(self, mock_db, mock_portfolio_service):
        """Test sector allocation calculation."""
        collector = PromptDataCollector(mock_db, mock_portfolio_service)

        class Position:
            def __init__(self, asset_type, value):
                self.asset_type = AssetType.STOCK if asset_type == "STOCK" else (AssetType.CRYPTO if asset_type == "CRYPTO" else AssetType.METAL)
                self.current_value = Decimal(str(value))
                self.sector = "Technology" if asset_type == "STOCK" else None

        positions = [
            Position("STOCK", 30000),
            Position("CRYPTO", 15000),
            Position("METAL", 5000),
        ]

        total_value = 50000.0
        allocation = collector._calculate_sector_allocation(positions, total_value)

        # New method only returns sector allocation for stocks
        assert "Technology" in allocation
        assert allocation["Technology"]["percentage"] == 100.0

    def test_calculate_sector_allocation_empty(self, mock_db, mock_portfolio_service):
        """Test sector allocation with no positions."""
        collector = PromptDataCollector(mock_db, mock_portfolio_service)

        allocation = collector._calculate_sector_allocation([], 0.0)
        assert allocation == {}

    def test_calculate_sector_allocation_zero_value(self, mock_db, mock_portfolio_service):
        """Test sector allocation with zero total value."""
        collector = PromptDataCollector(mock_db, mock_portfolio_service)

        class Position:
            def __init__(self):
                self.asset_type = AssetType.STOCK
                self.current_value = Decimal("0")
                self.sector = "Technology"

        allocation = collector._calculate_sector_allocation([Position()], 0.0)
        assert allocation == {}

    @pytest.mark.asyncio
    async def test_get_portfolio_performance(self, mock_db, mock_portfolio_service):
        """Test portfolio performance metrics collection."""
        collector = PromptDataCollector(mock_db, mock_portfolio_service)
        summary = await mock_portfolio_service.get_portfolio_pnl_summary()

        performance = await collector._get_portfolio_performance(summary)

        assert performance["current_pnl"] == 5000.00

    @pytest.mark.asyncio
    async def test_get_market_indices_success(self, collector_with_yahoo):
        """Test fetching market indices successfully."""
        indices = await collector_with_yahoo._get_market_indices()

        # Should have all 12 major indices (equities, risk, commodities, crypto)
        assert len(indices) == 12
        assert "^GSPC" in indices  # S&P 500
        assert "^DJI" in indices   # Dow Jones
        assert "^IXIC" in indices  # NASDAQ
        assert "^STOXX50E" in indices  # Euro Stoxx 50
        assert "^GDAXI" in indices  # DAX
        assert "^VIX" in indices  # VIX
        assert "^TNX" in indices  # 10Y Treasury
        assert "DX-Y.NYB" in indices  # Dollar Index
        assert "BTC-USD" in indices  # Bitcoin
        assert "GC=F" in indices   # Gold
        assert "CL=F" in indices   # Oil
        assert "HG=F" in indices   # Copper

        # Validate structure
        assert indices["^GSPC"]["price"] == 4500.50
        assert indices["^GSPC"]["change"] == 0.75

    @pytest.mark.asyncio
    async def test_get_market_indices_no_service(self, collector_without_yahoo):
        """Test market indices returns empty when service unavailable."""
        indices = await collector_without_yahoo._get_market_indices()
        assert indices == {}

    @pytest.mark.asyncio
    async def test_get_market_indices_partial_failure(self, mock_db, mock_portfolio_service):
        """Test market indices handles partial failures gracefully."""
        class PartialYahooService:
            async def get_quote(self, symbol):
                if symbol == "^GSPC":
                    class QuoteData:
                        current_price = 4500.50
                        day_change_percent = 0.75
                    return QuoteData()
                else:
                    raise Exception("API error")

        collector = PromptDataCollector(mock_db, mock_portfolio_service, PartialYahooService())
        indices = await collector._get_market_indices()

        # Should only have S&P 500, others skipped due to errors
        assert len(indices) == 1
        assert "^GSPC" in indices

    def test_format_holdings_list(self, mock_db, mock_portfolio_service):
        """Test formatting top holdings as readable string."""
        collector = PromptDataCollector(mock_db, mock_portfolio_service)

        holdings = [
            {'symbol': 'AAPL', 'value': 10000.50, 'allocation': 20.5, 'pnl': 15.25},
            {'symbol': 'BTC', 'value': 8500.00, 'allocation': 17.0, 'pnl': -5.75},
            {'symbol': 'GOLD', 'value': 3000.00, 'allocation': 6.0, 'pnl': 8.00}
        ]

        result = collector._format_holdings_list(holdings)

        # Check formatted string contains expected elements
        assert "AAPL: €10000.50 (20.5% of portfolio, +15.25% P&L)" in result
        assert "BTC: €8500.00 (17.0% of portfolio, -5.75% P&L)" in result
        assert "GOLD: €3000.00 (6.0% of portfolio, +8.00% P&L)" in result

        # Check each holding is on its own line
        lines = result.split('\n')
        assert len(lines) == 3

    def test_format_holdings_list_empty(self, mock_db, mock_portfolio_service):
        """Test formatting empty holdings list."""
        collector = PromptDataCollector(mock_db, mock_portfolio_service)

        result = collector._format_holdings_list([])
        assert result == "No holdings"
