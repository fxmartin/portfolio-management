# ABOUTME: Template rendering engine for AI prompts with type-safe variable substitution
# ABOUTME: Provides formatters for decimal, integer, array, and object types

from typing import Any, Dict
from decimal import Decimal


class PromptRenderer:
    """
    Template rendering engine for AI prompts.

    Safely renders prompt templates with portfolio data, ensuring
    type-safe variable substitution and proper formatting.
    """

    def __init__(self):
        self.formatters = {
            'decimal': self._format_decimal,
            'integer': self._format_integer,
            'array': self._format_array,
            'object': self._format_object,
            'string': str,
            'boolean': str
        }

    def render(
        self,
        prompt_text: str,
        template_vars: Dict[str, str],  # {var_name: type}
        data: Dict[str, Any]  # {var_name: value}
    ) -> str:
        """
        Render a prompt template with provided data.

        Args:
            prompt_text: Template string with {variable} placeholders
            template_vars: Dictionary mapping variable names to types
            data: Dictionary mapping variable names to values

        Returns:
            Rendered prompt string with all variables substituted

        Raises:
            ValueError: If required variables are missing or types are invalid
            TypeError: If value cannot be formatted as specified type
        """
        # Validate all required variables are present
        missing = set(template_vars.keys()) - set(data.keys())
        if missing:
            raise ValueError(f"Missing template variables: {missing}")

        # Format each value according to its type
        formatted_data = {}
        for var_name, var_type in template_vars.items():
            formatter = self.formatters.get(var_type)
            if not formatter:
                raise ValueError(f"Unknown type: {var_type}")

            try:
                formatted_data[var_name] = formatter(data[var_name])
            except (TypeError, ValueError, AttributeError) as e:
                raise TypeError(f"Cannot format {var_name} as {var_type}: {e}")

        # Template substitution using str.format()
        return prompt_text.format(**formatted_data)

    def _format_decimal(self, value: Any) -> str:
        """Format numeric value as decimal with 2 decimal places."""
        if value is None:
            return "0.00"
        if isinstance(value, (int, float, Decimal)):
            return f"{Decimal(str(value)):.2f}"
        raise TypeError(f"Cannot format {type(value).__name__} as decimal")

    def _format_integer(self, value: Any) -> str:
        """Format value as integer."""
        if value is None:
            return "0"
        return str(int(value))

    def _format_array(self, value: list) -> str:
        """
        Format list as readable string.

        For short lists (≤5 items), returns comma-separated values.
        For longer lists, shows first 5 items with count of remaining.
        """
        if not value:
            return "None"

        if len(value) <= 5:
            return ", ".join(str(v) for v in value)

        preview = ", ".join(str(v) for v in value[:5])
        remaining = len(value) - 5
        return f"{preview} (and {remaining} more)"

    def _format_object(self, value: dict) -> str:
        """
        Format dictionary as key: value pairs on separate lines.
        """
        if not value:
            return "None"

        lines = [f"{k}: {v}" for k, v in value.items()]
        return "\n".join(lines)


class PromptDataCollector:
    """
    Collects and formats portfolio data for prompt rendering.

    Aggregates data from portfolio service, position data, and
    market prices to provide context for AI analysis prompts.
    """

    def __init__(self, db, portfolio_service, yahoo_service=None):
        """
        Initialize data collector.

        Args:
            db: SQLAlchemy database session
            portfolio_service: PortfolioService instance for position data
            yahoo_service: Optional YahooFinanceService for market indices
        """
        self.db = db
        self.portfolio_service = portfolio_service
        self.yahoo_service = yahoo_service

    async def collect_global_data(self) -> Dict[str, Any]:
        """
        Collect comprehensive data for global market analysis prompt.

        Returns:
            Dictionary with portfolio_value, asset_allocation, sector_allocation,
            position_count, top_holdings, performance metrics, and market indices
        """
        summary = await self.portfolio_service.get_open_positions_summary(self.db)
        positions = await self.portfolio_service.get_all_positions(self.db)

        # Calculate sector allocation
        sector_allocation = self._calculate_sector_allocation(positions)

        # Get portfolio performance metrics
        performance = await self._get_portfolio_performance(summary)

        # Fetch market indices for context
        indices = await self._get_market_indices()

        # Prepare top holdings (top 10)
        sorted_positions = sorted(positions, key=lambda x: x.current_value, reverse=True)
        top_holdings = [
            {
                'symbol': p.symbol,
                'value': float(p.current_value),
                'allocation': float(p.portfolio_percentage),
                'pnl': float(p.unrealized_pnl_percentage)
            }
            for p in sorted_positions[:10]
        ]

        return {
            "portfolio_value": float(summary.total_value),
            "asset_allocation": {
                "stocks": float(summary.stocks_value),
                "stocks_pct": float(summary.stocks_percentage),
                "crypto": float(summary.crypto_value),
                "crypto_pct": float(summary.crypto_percentage),
                "metals": float(summary.metals_value),
                "metals_pct": float(summary.metals_percentage)
            },
            "sector_allocation": sector_allocation,
            "position_count": len(positions),
            "top_holdings": self._format_holdings_list(top_holdings),
            "performance": performance,
            "market_indices": indices,
            "total_unrealized_pnl": float(summary.total_unrealized_pnl),
            "total_unrealized_pnl_pct": float(summary.total_unrealized_pnl_percentage)
        }

    async def collect_position_data(self, symbol: str) -> Dict[str, Any]:
        """
        Collect data for position-specific analysis.

        Args:
            symbol: Asset symbol (e.g., "BTC", "AAPL")

        Returns:
            Dictionary with position details including quantity, prices,
            P&L metrics, and market context

        Raises:
            ValueError: If position not found
        """
        position = await self.portfolio_service.get_position(self.db, symbol)
        if not position:
            raise ValueError(f"Position not found: {symbol}")

        # Note: price_data would come from yahoo_finance_service in real implementation
        # For now, we'll use data already in the position object

        return {
            "symbol": position.symbol,
            "name": position.symbol,  # Could be enhanced with full name lookup
            "quantity": position.quantity,
            "current_price": position.current_price,
            "cost_basis": position.total_cost_basis,
            "unrealized_pnl": position.unrealized_pnl,
            "pnl_percentage": position.unrealized_pnl_percentage,
            "position_percentage": 0.0,  # Would calculate vs total portfolio
            "day_change": 0.0,  # Would come from price service
            "sector": "N/A",  # Would come from price service
            "asset_type": position.asset_type
        }

    async def collect_forecast_data(self, symbol: str) -> Dict[str, Any]:
        """
        Collect data for two-quarter forecast prompt.

        Args:
            symbol: Asset symbol (e.g., "BTC", "AAPL")

        Returns:
            Dictionary with current price, 52-week range, performance
            metrics, and market context

        Raises:
            ValueError: If position not found
        """
        position = await self.portfolio_service.get_position(self.db, symbol)
        if not position:
            raise ValueError(f"Position not found: {symbol}")

        # Note: Historical data would come from yahoo_finance_service
        # For now, return basic data structure

        return {
            "symbol": position.symbol,
            "name": position.symbol,
            "current_price": position.current_price,
            "week_52_low": 0.0,  # Would query historical data
            "week_52_high": 0.0,  # Would query historical data
            "performance_30d": 0.0,  # Would calculate from price history
            "performance_90d": 0.0,  # Would calculate from price history
            "sector": "N/A",
            "asset_type": position.asset_type,
            "market_context": "No historical data available"
        }

    def _calculate_sector_allocation(self, positions: list) -> Dict[str, float]:
        """
        Calculate portfolio allocation by sector.

        Args:
            positions: List of Position objects

        Returns:
            Dictionary mapping sector to percentage allocation
        """
        if not positions:
            return {}

        total_value = sum(float(p.current_value) for p in positions)
        if total_value == 0:
            return {}

        sectors = {}

        for p in positions:
            # Use asset_type as sector proxy
            # In future, could fetch sector data from Yahoo Finance
            sector = p.asset_type or "Unknown"
            if sector not in sectors:
                sectors[sector] = 0.0
            sectors[sector] += float(p.current_value)

        # Convert to percentages
        return {
            sector: round(value / total_value * 100, 2)
            for sector, value in sectors.items()
        }

    async def _get_portfolio_performance(self, summary: Any) -> Dict[str, Any]:
        """
        Get portfolio performance metrics.

        Args:
            summary: OpenPositionsSummary object

        Returns:
            Dictionary with current P&L metrics
        """
        return {
            "current_pnl": float(summary.total_unrealized_pnl),
            "current_pnl_pct": float(summary.total_unrealized_pnl_percentage),
            # Future: 24h, 7d, 30d historical changes from price_history table
        }

    async def _get_market_indices(self) -> Dict[str, Any]:
        """
        Fetch major market indices for context.

        Returns:
            Dictionary with price and change data for major indices
        """
        if not self.yahoo_service:
            return {}

        indices_symbols = [
            '^GSPC',    # S&P 500
            '^DJI',     # Dow Jones
            'BTC-USD',  # Bitcoin
            'GC=F'      # Gold Futures
        ]
        indices_data = {}

        for symbol in indices_symbols:
            try:
                price_data = await self.yahoo_service.get_price(symbol)
                indices_data[symbol] = {
                    'price': float(price_data.current_price),
                    'change': float(price_data.day_change_percent)
                }
            except Exception:
                # Skip indices that fail to fetch
                pass

        return indices_data

    def _format_holdings_list(self, holdings: list) -> str:
        """
        Format top holdings as readable string for prompt.

        Args:
            holdings: List of dictionaries with symbol, value, allocation, pnl

        Returns:
            Multi-line string with formatted holdings
        """
        if not holdings:
            return "No holdings"

        lines = []
        for h in holdings:
            lines.append(
                f"{h['symbol']}: €{h['value']:.2f} ({h['allocation']:.1f}% of portfolio, "
                f"{h['pnl']:+.2f}% P&L)"
            )
        return "\n".join(lines)
