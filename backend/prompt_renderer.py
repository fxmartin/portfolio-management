# ABOUTME: Template rendering engine for AI prompts with type-safe variable substitution
# ABOUTME: Provides formatters for decimal, integer, array, and object types

from typing import Any, Dict, Optional, List
from decimal import Decimal
from datetime import datetime, timedelta
from models import AssetType
import yfinance as yf


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
        summary = await self.portfolio_service.get_portfolio_pnl_summary()
        positions = await self.portfolio_service.get_all_positions()

        # Calculate sector allocation
        sector_allocation = self._calculate_sector_allocation(positions)

        # Get portfolio performance metrics
        performance = await self._get_portfolio_performance(summary)

        # Fetch market indices for context
        indices = await self._get_market_indices()

        # Prepare top holdings (top 10) - filter out positions with None values
        valid_positions = [p for p in positions if p.current_value is not None]
        sorted_positions = sorted(valid_positions, key=lambda x: x.current_value, reverse=True)

        # Calculate portfolio percentages manually
        total_portfolio_value = sum(p.current_value for p in valid_positions)
        top_holdings = []
        for p in sorted_positions[:10]:
            pct = (p.current_value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
            top_holdings.append({
                'symbol': p.symbol,
                'value': float(p.current_value),
                'allocation': round(pct, 2),
                'pnl': float(p.unrealized_pnl_percent) if p.unrealized_pnl_percent else 0.0
            })

        # Calculate portfolio value and asset allocation from positions
        total_value = sum(p.current_value for p in positions if p.current_value)

        return {
            "portfolio_value": float(total_value) if total_value else 0.0,
            "asset_allocation": sector_allocation,  # sector_allocation already has the breakdown
            "position_count": len(positions),
            "top_holdings": self._format_holdings_list(top_holdings),
            "performance": performance,
            "market_indices": indices,
            "total_unrealized_pnl": summary.get("total_unrealized_pnl", 0.0),
            "total_unrealized_pnl_pct": summary.get("total_unrealized_pnl_percentage", 0.0)
        }

    async def collect_position_data(self, symbol: str) -> Dict[str, Any]:
        """
        Collect enhanced data for position-specific analysis.

        Includes Yahoo Finance fundamentals, transaction context,
        performance metrics, and sector classification.

        Args:
            symbol: Asset symbol (e.g., "BTC", "AAPL")

        Returns:
            Dictionary with position details including:
            - Basic position data (quantity, prices, P&L)
            - Market fundamentals (sector, industry, 52-week range)
            - Transaction context (count, first purchase, holding period)
            - Performance metrics (volume, market cap)

        Raises:
            ValueError: If position not found
        """
        position = await self.portfolio_service.get_position(symbol)
        if not position:
            raise ValueError(f"Position not found: {symbol}")

        # Get fundamental data (if stock)
        fundamentals = {}
        if position.asset_type == AssetType.STOCK or position.asset_type == 'STOCK':
            fundamentals = await self._get_stock_fundamentals(symbol)

        # Get performance metrics
        performance = await self._get_position_performance(symbol)

        # Get transaction context
        transaction_count = await self._get_transaction_count(symbol)
        first_purchase = await self._get_first_purchase_date(symbol)
        holding_period = await self._get_holding_period(symbol)

        # Calculate portfolio percentage
        all_positions = await self.portfolio_service.get_all_positions()
        total_portfolio_value = sum(
            float(p.current_value)
            for p in all_positions
            if p.current_value is not None
        )
        position_pct = 0.0
        if total_portfolio_value > 0 and position.current_value:
            position_pct = (float(position.current_value) / total_portfolio_value) * 100

        return {
            # Position basics
            "symbol": position.symbol,
            "name": fundamentals.get('name') or position.asset_name or position.symbol,
            "quantity": position.quantity,
            "current_price": position.current_price,
            "cost_basis": position.total_cost_basis,
            "avg_cost_per_unit": position.avg_cost_basis,

            # P&L
            "unrealized_pnl": position.unrealized_pnl,
            "pnl_percentage": position.unrealized_pnl_percent,
            "position_percentage": round(position_pct, 2),

            # Market data
            "day_change": 0.0,  # Would come from price service

            # Performance metrics
            "performance_24h": performance.get('24h', 0.0),
            "performance_7d": performance.get('7d', 0.0),
            "performance_30d": performance.get('30d', 0.0),

            # Market context
            "week_52_low": float(fundamentals.get('fiftyTwoWeekLow', 0)),
            "week_52_high": float(fundamentals.get('fiftyTwoWeekHigh', 0)),
            "volume": fundamentals.get('volume', 0),
            "avg_volume": fundamentals.get('averageVolume', 0),

            # Classification
            "sector": fundamentals.get('sector', 'N/A'),
            "industry": fundamentals.get('industry', 'N/A'),
            "asset_type": position.asset_type,

            # Transaction context
            "transaction_count": transaction_count,
            "first_purchase_date": first_purchase,
            "holding_period_days": holding_period
        }

    async def collect_forecast_data(self, symbol: str) -> Dict[str, Any]:
        """
        Collect comprehensive data for two-quarter forecast prompt.

        Fetches historical prices, calculates performance metrics, and builds
        market context for generating accurate forecasts.

        Args:
            symbol: Asset symbol (e.g., "BTC", "AAPL")

        Returns:
            Dictionary with current price, 52-week range, performance
            metrics (30d/90d/180d/365d), volatility, and market context

        Raises:
            ValueError: If position not found
        """
        position = await self.portfolio_service.get_position(symbol)
        if not position:
            raise ValueError(f"Position not found: {symbol}")

        # Get historical prices (365 days)
        historical_prices = await self._get_historical_prices(symbol, days=365)

        # Calculate performance metrics
        performance = self._calculate_performance_metrics(historical_prices)

        # Build market context based on asset type
        market_context = await self._build_market_context(position.asset_type)

        # Calculate 52-week range
        week_52_low = min(historical_prices) if historical_prices else 0.0
        week_52_high = max(historical_prices) if historical_prices else 0.0

        return {
            "symbol": position.symbol,
            "name": position.symbol,
            "current_price": float(position.current_price),
            "week_52_low": float(week_52_low),
            "week_52_high": float(week_52_high),
            "performance_30d": performance['30d'],
            "performance_90d": performance['90d'],
            "performance_180d": performance['180d'],
            "performance_365d": performance['365d'],
            "volatility_30d": performance['volatility'],
            "sector": position.asset_type.value if isinstance(position.asset_type, AssetType) else str(position.asset_type),
            "asset_type": position.asset_type.value if isinstance(position.asset_type, AssetType) else str(position.asset_type),
            "market_context": market_context
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

        total_value = sum(float(p.current_value) for p in positions if p.current_value is not None)
        if total_value == 0:
            return {}

        sectors = {}

        for p in positions:
            # Use asset_type as sector proxy
            # In future, could fetch sector data from Yahoo Finance
            if p.current_value is None:
                continue
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
            "current_pnl": summary.get("total_unrealized_pnl", 0.0),
            "current_pnl_pct": summary.get("total_unrealized_pnl_percentage", 0.0),
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

    async def _get_stock_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch stock fundamentals from Yahoo Finance.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with fundamental data or empty dict on error
        """
        try:
            import yfinance as yf

            ticker = yf.Ticker(symbol)
            info = ticker.info

            return {
                'name': info.get('longName', symbol),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'fiftyTwoWeekLow': info.get('fiftyTwoWeekLow'),
                'fiftyTwoWeekHigh': info.get('fiftyTwoWeekHigh'),
                'volume': info.get('volume'),
                'averageVolume': info.get('averageVolume'),
                'marketCap': info.get('marketCap'),
                'peRatio': info.get('trailingPE')
            }
        except Exception:
            # Return empty dict if fundamentals fetch fails
            return {}

    async def _get_transaction_count(self, symbol: str) -> int:
        """
        Get count of transactions for a symbol.

        Args:
            symbol: Asset symbol

        Returns:
            Number of transactions for this symbol
        """
        from sqlalchemy import select, func
        from models import Transaction

        result = await self.db.execute(
            select(func.count()).select_from(Transaction).where(Transaction.symbol == symbol)
        )
        return result.scalar() or 0

    async def _get_first_purchase_date(self, symbol: str) -> Optional[datetime]:
        """
        Get the date of first purchase for a symbol.

        Args:
            symbol: Asset symbol

        Returns:
            DateTime of first purchase or None if no purchases
        """
        from sqlalchemy import select
        from models import Transaction

        result = await self.db.execute(
            select(Transaction.transaction_date)
            .where(Transaction.symbol == symbol)
            .where(Transaction.transaction_type.in_(['BUY', 'DEPOSIT', 'STAKING', 'AIRDROP']))
            .order_by(Transaction.transaction_date.asc())
            .limit(1)
        )
        return result.scalar()

    async def _get_holding_period(self, symbol: str) -> int:
        """
        Calculate holding period in days for a symbol.

        Args:
            symbol: Asset symbol

        Returns:
            Number of days since first purchase, or 0 if no purchases
        """
        first_date = await self._get_first_purchase_date(symbol)
        if not first_date:
            return 0

        return (datetime.utcnow() - first_date).days

    async def _get_position_performance(self, symbol: str) -> Dict[str, float]:
        """
        Get position performance metrics.

        For MVP, returns placeholder values. In future, would calculate
        from price_history table.

        Args:
            symbol: Asset symbol

        Returns:
            Dictionary with performance metrics for 24h, 7d, 30d periods
        """
        # MVP: Return placeholder values
        # Future: Query price_history table and calculate actual performance
        return {
            '24h': 0.0,
            '7d': 0.0,
            '30d': 0.0
        }

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

    async def _get_historical_prices(self, symbol: str, days: int = 365) -> List[float]:
        """
        Fetch historical prices from Yahoo Finance.

        Args:
            symbol: Asset symbol
            days: Number of days of history to fetch (default: 365)

        Returns:
            List of closing prices (oldest to newest)
        """
        try:
            # Transform symbol if needed (for ETFs with exchange suffixes)
            transformed_symbol = self._transform_symbol_for_yfinance(symbol)

            ticker = yf.Ticker(transformed_symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            hist = ticker.history(start=start_date, end=end_date)

            if hist.empty:
                return []

            return hist['Close'].tolist()
        except Exception:
            # Return empty list on error (graceful degradation)
            return []

    def _calculate_performance_metrics(self, prices: List[float]) -> Dict[str, float]:
        """
        Calculate performance metrics from price history.

        Computes percentage returns for 30d, 90d, 180d, 365d periods
        and 30-day volatility (annualized standard deviation).

        Args:
            prices: List of prices (oldest to newest)

        Returns:
            Dictionary with performance metrics
        """
        if not prices or len(prices) < 2:
            return {
                '30d': 0.0,
                '90d': 0.0,
                '180d': 0.0,
                '365d': 0.0,
                'volatility': 0.0
            }

        current = prices[-1]

        # Calculate returns for different periods
        perf_30d = ((current - prices[-min(30, len(prices))]) / prices[-min(30, len(prices))] * 100) if len(prices) >= 2 else 0.0
        perf_90d = ((current - prices[-min(90, len(prices))]) / prices[-min(90, len(prices))] * 100) if len(prices) >= 2 else 0.0
        perf_180d = ((current - prices[-min(180, len(prices))]) / prices[-min(180, len(prices))] * 100) if len(prices) >= 2 else 0.0
        perf_365d = ((current - prices[0]) / prices[0] * 100) if len(prices) >= 2 else 0.0

        # Calculate 30-day volatility (annualized)
        volatility = 0.0
        if len(prices) >= 30:
            # Get last 30 prices
            recent_prices = prices[-30:]
            # Calculate daily returns
            returns = [(recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1]
                      for i in range(1, len(recent_prices))]
            # Calculate standard deviation
            if returns:
                mean_return = sum(returns) / len(returns)
                variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
                daily_vol = variance ** 0.5
                # Annualize (252 trading days)
                volatility = daily_vol * (252 ** 0.5) * 100

        return {
            '30d': round(perf_30d, 2),
            '90d': round(perf_90d, 2),
            '180d': round(perf_180d, 2),
            '365d': round(perf_365d, 2),
            'volatility': round(volatility, 2)
        }

    async def _build_market_context(self, asset_type: AssetType) -> str:
        """
        Build narrative market context based on asset type.

        Fetches relevant market indices and constructs a narrative
        summary of current market conditions.

        Args:
            asset_type: Type of asset (stocks, crypto, metals)

        Returns:
            String describing market context
        """
        context_parts = []

        try:
            asset_type_str = asset_type.value if isinstance(asset_type, AssetType) else str(asset_type)

            # Get relevant indices based on asset type (uppercase comparison)
            if asset_type_str.upper() == 'STOCK':
                sp500_price = await self.yahoo_service.get_price('^GSPC')
                context_parts.append(
                    f"S&P 500: {sp500_price.day_change_percent:+.2f}% today"
                )
            elif asset_type_str.upper() == 'CRYPTO':
                btc_price = await self.yahoo_service.get_price('BTC-EUR')
                context_parts.append(
                    f"Bitcoin (market leader): {btc_price.day_change_percent:+.2f}% today"
                )
            elif asset_type_str.upper() == 'METAL':
                gold_price = await self.yahoo_service.get_price('GC=F')
                context_parts.append(
                    f"Gold: {gold_price.day_change_percent:+.2f}% today"
                )

            # Add general macro context
            context_parts.append("Market showing mixed signals with ongoing volatility")

            return ". ".join(context_parts) if context_parts else "Market context unavailable"

        except Exception:
            # Graceful degradation if index prices unavailable
            return "Market context unavailable"

    def _transform_symbol_for_yfinance(self, symbol: str) -> str:
        """
        Transform internal symbol to Yahoo Finance format.

        Some ETFs require exchange suffixes for Yahoo Finance.

        Args:
            symbol: Internal symbol

        Returns:
            Yahoo Finance compatible symbol
        """
        # ETF mappings (same as YahooFinanceService)
        ETF_MAPPINGS = {
            "AMEM": "AMEM.BE",  # iShares MSCI Emerging Markets (Brussels)
            "MWOQ": "MWOQ.BE",  # SPDR MSCI World (Brussels)
        }

        return ETF_MAPPINGS.get(symbol, symbol)
