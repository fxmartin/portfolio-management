# ABOUTME: Template rendering engine for AI prompts with type-safe variable substitution
# ABOUTME: Provides formatters for decimal, integer, array, and object types

from typing import Any, Dict, Optional, List
from decimal import Decimal
from datetime import datetime, timedelta, timezone, UTC
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
        for var_name, var_type_or_obj in template_vars.items():
            # Handle both old format (string) and new format (dict with "type" key)
            if isinstance(var_type_or_obj, dict):
                var_type = var_type_or_obj.get("type", "string")
            else:
                var_type = var_type_or_obj

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

    def __init__(
        self,
        db,
        portfolio_service,
        yahoo_service=None,
        twelve_data_service=None,
        alpha_vantage_service=None,
        coingecko_service=None
    ):
        """
        Initialize data collector.

        Args:
            db: SQLAlchemy database session
            portfolio_service: PortfolioService instance for position data
            yahoo_service: Optional YahooFinanceService for market indices
            twelve_data_service: Optional TwelveDataService for European stocks (primary)
            alpha_vantage_service: Optional AlphaVantageService for fallback
            coingecko_service: Optional CoinGeckoService for crypto fundamentals
        """
        self.db = db
        self.portfolio_service = portfolio_service
        self.yahoo_service = yahoo_service
        self.twelve_data_service = twelve_data_service
        self.alpha_vantage_service = alpha_vantage_service
        self.coingecko_service = coingecko_service

    async def collect_global_data(self) -> Dict[str, Any]:
        """
        Collect comprehensive data for global market analysis prompt.

        Returns:
            Dictionary with portfolio_value, asset_allocation, sector_allocation,
            position_count, top_holdings, performance metrics, and market indices
        """
        summary = await self.portfolio_service.get_portfolio_pnl_summary()
        positions = await self.portfolio_service.get_all_positions()

        # Calculate total value for sector allocation
        valid_positions_for_allocation = [p for p in positions if p.current_value is not None]
        total_value = sum(float(p.current_value) for p in valid_positions_for_allocation)

        # Calculate sector allocation
        sector_allocation = self._calculate_sector_allocation(valid_positions_for_allocation, total_value)

        # Get portfolio performance metrics
        performance = await self._get_portfolio_performance(summary)

        # Fetch market indices for context
        indices = await self._get_market_indices()
        market_context = self._format_market_indices(indices)
        market_indicators_data = self._build_market_indicators_response(indices)

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

        # Fetch global crypto market data (if coingecko_service available)
        global_crypto_context = ""
        global_crypto_data = None
        if self.coingecko_service:
            try:
                crypto_data = await self.coingecko_service.get_global_market_data()
                global_crypto_data = {
                    "total_market_cap_eur": crypto_data.total_market_cap_eur,
                    "total_volume_24h_eur": crypto_data.total_volume_24h_eur,
                    "btc_dominance": float(crypto_data.btc_dominance),
                    "eth_dominance": float(crypto_data.eth_dominance),
                    "active_cryptocurrencies": crypto_data.active_cryptocurrencies,
                    "markets": crypto_data.markets,
                    "market_cap_change_24h": float(crypto_data.market_cap_change_24h),
                    "defi_market_cap_eur": crypto_data.defi_market_cap_eur,
                    "defi_dominance": float(crypto_data.defi_dominance) if crypto_data.defi_dominance else 0,
                    "defi_24h_volume_eur": crypto_data.defi_24h_volume_eur,
                    "fear_greed_value": crypto_data.fear_greed_value,
                    "fear_greed_classification": crypto_data.fear_greed_classification
                }

                # Build context string for Claude prompt
                market_cap_b = crypto_data.total_market_cap_eur / 1_000_000_000
                volume_b = crypto_data.total_volume_24h_eur / 1_000_000_000

                # Build base context
                context_lines = [
                    "Global Crypto Market Overview (CoinGecko):",
                    f"- Total Market Cap: €{market_cap_b:.1f}B ({crypto_data.market_cap_change_24h:+.1f}% 24h)",
                    f"- 24h Trading Volume: €{volume_b:.1f}B",
                    f"- Bitcoin Dominance: {crypto_data.btc_dominance:.1f}%",
                    f"- Ethereum Dominance: {crypto_data.eth_dominance:.1f}%",
                    f"- Active Cryptocurrencies: {crypto_data.active_cryptocurrencies:,}"
                ]

                # Add Fear & Greed Index if available
                if crypto_data.fear_greed_value and crypto_data.fear_greed_classification:
                    context_lines.append(f"- Fear & Greed Index: {crypto_data.fear_greed_value}/100 ({crypto_data.fear_greed_classification})")

                # Add DeFi data if available
                if crypto_data.defi_market_cap_eur and crypto_data.defi_dominance:
                    defi_cap_b = crypto_data.defi_market_cap_eur / 1_000_000_000
                    context_lines.append(f"- DeFi Market Cap: €{defi_cap_b:.1f}B ({crypto_data.defi_dominance:.1f}% of total)")

                global_crypto_context = "\n".join(context_lines)

                print(f"[Global Data] Fetched global crypto market data: Market Cap €{market_cap_b:.1f}B, BTC Dom {crypto_data.btc_dominance:.1f}%")
            except Exception as e:
                print(f"[Global Data] Failed to fetch global crypto market data: {e}")

        return {
            "portfolio_value": float(total_value) if total_value else 0.0,
            "asset_allocation": sector_allocation,  # sector_allocation already has the breakdown
            "position_count": len(positions),
            "top_holdings": self._format_holdings_list(top_holdings),
            "performance": performance,
            "market_indices": indices,
            "market_context": market_context,  # Formatted string for Claude
            "total_unrealized_pnl": summary.get("total_unrealized_pnl", 0.0),
            "total_unrealized_pnl_pct": summary.get("total_unrealized_pnl_percentage", 0.0),
            "global_crypto_context": global_crypto_context,
            "global_crypto_market": global_crypto_data,  # Raw data for frontend display
            "market_indicators": market_indicators_data  # Structured market indicators for frontend display
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

        # Get fundamental data based on asset type
        fundamentals = {}
        crypto_fundamentals = None

        # For crypto: fetch CoinGecko fundamentals
        if (position.asset_type == AssetType.CRYPTO or position.asset_type == 'CRYPTO') and self.coingecko_service:
            try:
                crypto_fundamentals = await self.coingecko_service.get_fundamentals(symbol)
                fundamentals = {
                    'name': crypto_fundamentals.name,
                    'sector': 'Cryptocurrency',
                    'industry': 'Digital Assets',
                    'volume': crypto_fundamentals.total_volume_24h,
                    'averageVolume': None,
                    'marketCap': crypto_fundamentals.market_cap,
                    'fiftyTwoWeekLow': None,  # Will use ATL instead
                    'fiftyTwoWeekHigh': None,  # Will use ATH instead
                    'peRatio': None
                }
                print(f"[Position Data] CoinGecko fundamentals for {symbol}: Rank #{crypto_fundamentals.market_cap_rank}, MCap €{crypto_fundamentals.market_cap:,.0f}")
            except Exception as e:
                print(f"[Position Data] CoinGecko failed for {symbol}: {e}")
                # Graceful fallback - continue without crypto fundamentals

        # For stocks: Use Twelve Data if available (better for European stocks), fallback to Yahoo Finance
        elif position.asset_type == AssetType.STOCK or position.asset_type == 'STOCK':
            if self.twelve_data_service:
                try:
                    # Try Twelve Data first for accurate European ETF data
                    price_data = await self.twelve_data_service.get_quote(symbol)
                    fundamentals = {
                        'name': price_data.asset_name or symbol,
                        'sector': None,  # Twelve Data doesn't provide sector in quote
                        'industry': None,
                        'fiftyTwoWeekLow': None,  # Not in quote endpoint
                        'fiftyTwoWeekHigh': None,
                        'volume': price_data.volume,
                        'averageVolume': None,
                        'marketCap': None,
                        'peRatio': None
                    }
                    print(f"[Position Data] Using Twelve Data fundamentals for {symbol}: {price_data.asset_name}")
                except Exception as e:
                    print(f"[Position Data] Twelve Data failed for {symbol}, falling back to Yahoo: {e}")
                    fundamentals = await self._get_stock_fundamentals(symbol)
            else:
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

        # Build response with crypto-specific fields if available
        response = {
            # Position basics
            "symbol": position.symbol,
            "name": fundamentals.get('name') or position.asset_name or position.symbol,
            "quantity": position.quantity,
            "current_value": position.current_value,
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
            "week_52_low": float(fundamentals.get('fiftyTwoWeekLow') or 0),
            "week_52_high": float(fundamentals.get('fiftyTwoWeekHigh') or 0),
            "volume": fundamentals.get('volume') or 0,
            "avg_volume": fundamentals.get('averageVolume') or 0,

            # Classification
            "sector": fundamentals.get('sector', 'N/A'),
            "industry": fundamentals.get('industry', 'N/A'),
            "asset_type": position.asset_type,

            # Transaction context
            "transaction_count": transaction_count,
            "first_purchase_date": first_purchase,
            "holding_period_days": holding_period
        }

        # Add Fear & Greed Index context for crypto positions
        fear_greed_context = ""
        if (position.asset_type == AssetType.CRYPTO or position.asset_type == 'CRYPTO') and self.coingecko_service:
            try:
                global_crypto_data = await self.coingecko_service.get_global_market_data()
                if global_crypto_data.fear_greed_value and global_crypto_data.fear_greed_classification:
                    fear_greed_context = f"\n- Fear & Greed Index: {global_crypto_data.fear_greed_value}/100 ({global_crypto_data.fear_greed_classification})"
            except Exception as e:
                print(f"[Position Data] Failed to fetch Fear & Greed for {symbol}: {e}")

        # Add crypto-specific CoinGecko fields if available
        crypto_context = ""
        if crypto_fundamentals:
            # Build rich crypto context string
            # Use timezone-aware datetime to match CoinGecko's timezone-aware dates
            now_utc = datetime.now(timezone.utc)
            days_since_ath = (now_utc - crypto_fundamentals.ath_date).days
            supply_text = f"{crypto_fundamentals.circulating_supply:,.0f}"
            if crypto_fundamentals.max_supply:
                supply_pct = (crypto_fundamentals.circulating_supply / crypto_fundamentals.max_supply * 100)
                supply_text += f" / {crypto_fundamentals.max_supply:,.0f} ({supply_pct:.1f}% of max)"
            else:
                supply_text += " (no max supply)"

            crypto_context = f"""
Cryptocurrency Fundamentals (CoinGecko):
- Market Cap: €{crypto_fundamentals.market_cap:,.0f} (Rank #{crypto_fundamentals.market_cap_rank})
- Supply: {supply_text}
- ATH: €{crypto_fundamentals.ath:.2f} on {crypto_fundamentals.ath_date.strftime('%Y-%m-%d')} ({days_since_ath} days ago)
  Currently {crypto_fundamentals.ath_change_percentage:+.1f}% from ATH
- ATL: €{crypto_fundamentals.atl:.2f} on {crypto_fundamentals.atl_date.strftime('%Y-%m-%d')}
  Currently {crypto_fundamentals.atl_change_percentage:+.1f}% from ATL
- Performance: 7d {crypto_fundamentals.price_change_percentage_7d or 0:+.1f}%, 30d {crypto_fundamentals.price_change_percentage_30d or 0:+.1f}%, 1y {crypto_fundamentals.price_change_percentage_1y or 0:+.1f}%
- All-Time ROI (ATL→ATH): {crypto_fundamentals.all_time_high_roi or 0:+,.0f}%
""".strip()

            response.update({
                # CoinGecko crypto fundamentals
                "market_cap": float(crypto_fundamentals.market_cap),
                "market_cap_rank": crypto_fundamentals.market_cap_rank or 0,
                "total_volume_24h": float(crypto_fundamentals.total_volume_24h),
                "circulating_supply": float(crypto_fundamentals.circulating_supply) if crypto_fundamentals.circulating_supply else 0,
                "max_supply": float(crypto_fundamentals.max_supply) if crypto_fundamentals.max_supply else 0,
                "ath": float(crypto_fundamentals.ath),
                "ath_date": crypto_fundamentals.ath_date.strftime('%Y-%m-%d'),
                "ath_change_percentage": float(crypto_fundamentals.ath_change_percentage),
                "atl": float(crypto_fundamentals.atl),
                "atl_date": crypto_fundamentals.atl_date.strftime('%Y-%m-%d'),
                "atl_change_percentage": float(crypto_fundamentals.atl_change_percentage),
                "price_change_percentage_7d": float(crypto_fundamentals.price_change_percentage_7d) if crypto_fundamentals.price_change_percentage_7d else 0,
                "price_change_percentage_30d": float(crypto_fundamentals.price_change_percentage_30d) if crypto_fundamentals.price_change_percentage_30d else 0,
                "price_change_percentage_1y": float(crypto_fundamentals.price_change_percentage_1y) if crypto_fundamentals.price_change_percentage_1y else 0,
                "all_time_roi": float(crypto_fundamentals.all_time_high_roi) if crypto_fundamentals.all_time_high_roi else 0,
                # Override 52-week range with ATL/ATH for crypto
                "week_52_low": float(crypto_fundamentals.atl),
                "week_52_high": float(crypto_fundamentals.ath),
                "crypto_context": crypto_context
            })
        else:
            # Add empty crypto_context for non-crypto or when CoinGecko unavailable
            response["crypto_context"] = ""

        # Add fear_greed_context to response
        response["fear_greed_context"] = fear_greed_context

        # Add portfolio context for strategic recommendations (F8.4-003)
        portfolio_context_data = await self._collect_portfolio_context()
        response["portfolio_context"] = self._format_portfolio_context(portfolio_context_data)

        return response

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

        # Get fundamentals for 52-week range (more reliable than historical prices for some ETFs)
        fundamentals = await self._get_stock_fundamentals(symbol)

        # Calculate 52-week range with fallback to fundamentals
        # Yahoo Finance historical data may be incomplete for European ETFs
        if historical_prices and len(historical_prices) > 1:
            week_52_low = min(historical_prices)
            week_52_high = max(historical_prices)
        else:
            # Fallback to fundamentals data
            week_52_low = fundamentals.get('fiftyTwoWeekLow', 0.0)
            week_52_high = fundamentals.get('fiftyTwoWeekHigh', 0.0)

        return {
            "symbol": position.symbol,
            "name": position.symbol,
            "current_price": float(position.current_price),
            "week_52_low": float(week_52_low) if week_52_low else 0.0,
            "week_52_high": float(week_52_high) if week_52_high else 0.0,
            "performance_30d": performance['30d'],
            "performance_90d": performance['90d'],
            "performance_180d": performance['180d'],
            "performance_365d": performance['365d'],
            "volatility_30d": performance['volatility'],
            "sector": position.asset_type.value if isinstance(position.asset_type, AssetType) else str(position.asset_type),
            "asset_type": position.asset_type.value if isinstance(position.asset_type, AssetType) else str(position.asset_type),
            "market_context": market_context
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
        Fetch major market indices for comprehensive global context.

        Returns:
            Dictionary with price and change data organized by category:
            - equities: Major stock indices (US & EU)
            - risk: Volatility, yields, dollar strength
            - commodities: Gold, oil, copper
            - crypto: Bitcoin
        """
        if not self.yahoo_service:
            return {}

        # Phase 1: Critical global market indicators
        indices_config = {
            # Equities
            '^GSPC': {'name': 'S&P 500', 'category': 'equities'},
            '^DJI': {'name': 'Dow Jones', 'category': 'equities'},
            '^IXIC': {'name': 'NASDAQ', 'category': 'equities'},
            '^STOXX50E': {'name': 'Euro Stoxx 50', 'category': 'equities'},
            '^GDAXI': {'name': 'DAX', 'category': 'equities'},

            # Risk Indicators (CRITICAL)
            '^VIX': {'name': 'VIX (Volatility)', 'category': 'risk'},
            '^TNX': {'name': '10Y Treasury Yield', 'category': 'risk'},
            'DX-Y.NYB': {'name': 'US Dollar Index', 'category': 'risk'},

            # Commodities
            'GC=F': {'name': 'Gold', 'category': 'commodities'},
            'CL=F': {'name': 'WTI Oil', 'category': 'commodities'},
            'HG=F': {'name': 'Copper', 'category': 'commodities'},

            # Crypto
            'BTC-USD': {'name': 'Bitcoin', 'category': 'crypto'},
        }

        indices_data = {}

        for symbol, config in indices_config.items():
            try:
                price_data = await self.yahoo_service.get_quote(symbol)
                indices_data[symbol] = {
                    'name': config['name'],
                    'category': config['category'],
                    'price': float(price_data.current_price),
                    'change': float(price_data.day_change_percent)
                }
            except Exception as e:
                # Skip indices that fail to fetch, but log for debugging
                print(f"[Market Indices] Failed to fetch {config['name']} ({symbol}): {e}")
                pass

        return indices_data

    def _format_market_indices(self, indices: Dict[str, Any]) -> str:
        """
        Format market indices data into readable context string for Claude.

        Args:
            indices: Dictionary of market data from _get_market_indices()

        Returns:
            Formatted string with categorized market data
        """
        if not indices:
            return "Market data unavailable"

        # Group by category
        categories = {
            'equities': [],
            'risk': [],
            'commodities': [],
            'crypto': []
        }

        for symbol, data in indices.items():
            category = data.get('category', 'other')
            if category in categories:
                name = data['name']
                price = data['price']
                change = data['change']
                sign = '+' if change >= 0 else ''
                categories[category].append(f"{name}: {price:.2f} ({sign}{change:.2f}%)")

        # Build formatted string
        lines = ["Global Market Snapshot:"]

        if categories['equities']:
            lines.append("\nEquities:")
            for line in categories['equities']:
                lines.append(f"  - {line}")

        if categories['risk']:
            lines.append("\nRisk Indicators:")
            for line in categories['risk']:
                lines.append(f"  - {line}")
            # Add VIX interpretation
            vix_data = indices.get('^VIX')
            if vix_data:
                vix = vix_data['price']
                if vix < 15:
                    lines.append("    → Low volatility (complacent market)")
                elif vix < 20:
                    lines.append("    → Normal volatility")
                elif vix < 30:
                    lines.append("    → Elevated fear")
                else:
                    lines.append("    → High panic/crisis levels")

        if categories['commodities']:
            lines.append("\nCommodities:")
            for line in categories['commodities']:
                lines.append(f"  - {line}")

        if categories['crypto']:
            lines.append("\nCrypto:")
            for line in categories['crypto']:
                lines.append(f"  - {line}")

        return "\n".join(lines)

    def _build_market_indicators_response(self, indices: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert raw market indices to structured GlobalMarketIndicators format.

        Args:
            indices: Dictionary of market data from _get_market_indices()

        Returns:
            Dictionary with categorized market indicators or None if no data
        """
        if not indices:
            return None

        # Group indicators by category
        categorized = {
            'equities': [],
            'risk': [],
            'commodities': [],
            'crypto': []
        }

        for symbol, data in indices.items():
            category = data.get('category', 'other')
            if category not in categorized:
                continue

            # Get VIX interpretation if this is the VIX indicator
            interpretation = None
            if symbol == '^VIX':
                vix = data['price']
                if vix < 15:
                    interpretation = "Low volatility (complacent market)"
                elif vix < 20:
                    interpretation = "Normal volatility"
                elif vix < 30:
                    interpretation = "Elevated fear"
                else:
                    interpretation = "High panic/crisis levels"

            indicator = {
                'symbol': symbol,
                'name': data['name'],
                'price': data['price'],
                'change_percent': data['change'],
                'category': category,
                'interpretation': interpretation
            }

            categorized[category].append(indicator)

        return categorized

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

            # Transform symbol for Yahoo Finance (handles ETF exchange suffixes)
            transformed_symbol = self._transform_symbol_for_yfinance(symbol)
            ticker = yf.Ticker(transformed_symbol)
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
        Fetch historical prices with fallback chain:
        1. Twelve Data (primary - paid, best European coverage)
        2. Yahoo Finance (secondary - free, fast)
        3. Alpha Vantage (tertiary - emergency fallback)

        Args:
            symbol: Asset symbol
            days: Number of days of history to fetch (default: 365)

        Returns:
            List of closing prices (oldest to newest)
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Try Twelve Data first (primary source)
        if hasattr(self, 'twelve_data_service') and self.twelve_data_service:
            try:
                print(f"[Historical Prices] Trying Twelve Data for {symbol}")
                prices_dict = await self.twelve_data_service.get_historical_daily(
                    symbol, start_date, end_date
                )
                if prices_dict:
                    # Convert dict to sorted list
                    sorted_dates = sorted(prices_dict.keys())
                    prices_list = [float(prices_dict[date]) for date in sorted_dates]
                    print(f"[Historical Prices] ✓ Twelve Data: {len(prices_list)} data points")
                    return prices_list
            except Exception as e:
                print(f"[Historical Prices] Twelve Data failed: {e}")

        # Try Yahoo Finance (secondary source)
        try:
            print(f"[Historical Prices] Trying Yahoo Finance for {symbol}")
            # Transform symbol if needed (for ETFs with exchange suffixes)
            transformed_symbol = self._transform_symbol_for_yfinance(symbol)

            ticker = yf.Ticker(transformed_symbol)
            hist = ticker.history(start=start_date, end=end_date)

            if not hist.empty:
                prices_list = hist['Close'].tolist()
                print(f"[Historical Prices] ✓ Yahoo Finance: {len(prices_list)} data points")
                return prices_list
        except Exception as e:
            print(f"[Historical Prices] Yahoo Finance failed: {e}")

        # Try Alpha Vantage (tertiary fallback)
        if hasattr(self, 'alpha_vantage_service') and self.alpha_vantage_service:
            try:
                print(f"[Historical Prices] Trying Alpha Vantage for {symbol}")
                prices_dict = await self.alpha_vantage_service.get_historical_daily(
                    symbol, start_date, end_date
                )
                if prices_dict:
                    # Convert dict to sorted list
                    sorted_dates = sorted(prices_dict.keys())
                    prices_list = [float(prices_dict[date]) for date in sorted_dates]
                    print(f"[Historical Prices] ✓ Alpha Vantage: {len(prices_list)} data points")
                    return prices_list
            except Exception as e:
                print(f"[Historical Prices] Alpha Vantage failed: {e}")

        # All sources failed - graceful degradation
        print(f"[Historical Prices] ✗ All sources failed for {symbol}")
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

    async def _collect_portfolio_context(self) -> Dict[str, Any]:
        """
        Collect full portfolio context for strategic position analysis.

        Gathers asset allocation, sector breakdown, top holdings, and
        concentration metrics to enable portfolio-aware recommendations.

        Returns:
            Dictionary with comprehensive portfolio context including:
            - total_value: Total portfolio value in EUR
            - position_count: Number of positions
            - asset_allocation: Breakdown by asset type (stocks/crypto/metals)
            - sector_allocation: Breakdown by sector (stocks only)
            - top_10_holdings: Top 10 positions by weight
            - concentration_metrics: Risk metrics (top 3, max sector, max single asset)
        """
        positions = await self.portfolio_service.get_all_positions()

        if not positions:
            return {
                "total_value": 0.0,
                "position_count": 0,
                "asset_allocation": {},
                "sector_allocation": {},
                "top_10_holdings": [],
                "concentration_metrics": {
                    "top_3_weight": 0.0,
                    "single_sector_max": 0.0,
                    "single_asset_max": 0.0
                }
            }

        # Calculate total portfolio value (filter out None values)
        valid_positions = [p for p in positions if p.current_value is not None]
        total_value = sum(float(p.current_value) for p in valid_positions)

        # Calculate asset allocation
        asset_allocation = self._calculate_asset_allocation(valid_positions, total_value)

        # Calculate sector allocation (stocks only)
        sector_allocation = self._calculate_sector_allocation(valid_positions, total_value)

        # Get top 10 holdings
        top_holdings = self._get_top_holdings(valid_positions, total_value)

        # Calculate concentration metrics
        concentration_metrics = self._calculate_concentration_metrics(
            valid_positions,
            total_value,
            sector_allocation
        )

        return {
            "total_value": total_value,
            "position_count": len(positions),
            "asset_allocation": asset_allocation,
            "sector_allocation": sector_allocation,
            "top_10_holdings": top_holdings,
            "concentration_metrics": concentration_metrics
        }

    def _calculate_asset_allocation(self, positions: list, total_value: float) -> Dict[str, Any]:
        """
        Calculate portfolio allocation by asset type.

        Args:
            positions: List of Position objects
            total_value: Total portfolio value

        Returns:
            Dictionary mapping asset type to {value, percentage, count}
        """
        if total_value == 0:
            return {}

        allocation = {}

        for position in positions:
            asset_type_str = position.asset_type.value if isinstance(position.asset_type, AssetType) else str(position.asset_type)

            if asset_type_str not in allocation:
                allocation[asset_type_str] = {
                    "value": 0.0,
                    "percentage": 0.0,
                    "count": 0
                }

            allocation[asset_type_str]["value"] += float(position.current_value)
            allocation[asset_type_str]["count"] += 1

        # Calculate percentages
        for asset_type in allocation:
            allocation[asset_type]["percentage"] = round(
                (allocation[asset_type]["value"] / total_value) * 100, 2
            )

        return allocation

    def _calculate_sector_allocation(self, positions: list, total_value: float) -> Dict[str, Any]:
        """
        Calculate sector allocation for stock positions only.

        Args:
            positions: List of Position objects
            total_value: Total portfolio value

        Returns:
            Dictionary mapping sector to {value, percentage, count}
        """
        # Filter to stock positions only
        stock_positions = [
            p for p in positions
            if (p.asset_type == AssetType.STOCK or p.asset_type == 'STOCK')
            and hasattr(p, 'sector') and p.sector
        ]

        if not stock_positions:
            return {}

        # Calculate total stock value
        total_stock_value = sum(float(p.current_value) for p in stock_positions)

        if total_stock_value == 0:
            return {}

        allocation = {}

        for position in stock_positions:
            sector = position.sector

            if sector not in allocation:
                allocation[sector] = {
                    "value": 0.0,
                    "percentage": 0.0,
                    "count": 0
                }

            allocation[sector]["value"] += float(position.current_value)
            allocation[sector]["count"] += 1

        # Calculate percentages relative to total stock value
        for sector in allocation:
            allocation[sector]["percentage"] = round(
                (allocation[sector]["value"] / total_stock_value) * 100, 2
            )

        return allocation

    def _get_top_holdings(self, positions: list, total_value: float) -> List[Dict[str, Any]]:
        """
        Get top 10 positions by portfolio weight.

        Args:
            positions: List of Position objects
            total_value: Total portfolio value

        Returns:
            List of holdings with symbol, value, weight, asset_type, sector
        """
        if total_value == 0:
            return []

        # Sort positions by value (descending)
        sorted_positions = sorted(
            positions,
            key=lambda p: float(p.current_value),
            reverse=True
        )

        holdings = []
        for position in sorted_positions[:10]:  # Top 10
            weight = (float(position.current_value) / total_value) * 100
            asset_type_str = position.asset_type.value if isinstance(position.asset_type, AssetType) else str(position.asset_type)

            holding = {
                "symbol": position.symbol,
                "value": float(position.current_value),
                "weight": round(weight, 2),
                "asset_type": asset_type_str
            }

            # Add sector for stocks
            if hasattr(position, 'sector') and position.sector:
                holding["sector"] = position.sector

            holdings.append(holding)

        return holdings

    def _calculate_concentration_metrics(
        self,
        positions: list,
        total_value: float,
        sector_allocation: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate portfolio concentration risk metrics.

        Args:
            positions: List of Position objects
            total_value: Total portfolio value
            sector_allocation: Sector allocation dictionary

        Returns:
            Dictionary with top_3_weight, single_sector_max, single_asset_max
        """
        if total_value == 0:
            return {
                "top_3_weight": 0.0,
                "single_sector_max": 0.0,
                "single_asset_max": 0.0
            }

        # Sort positions by value
        sorted_positions = sorted(
            positions,
            key=lambda p: float(p.current_value),
            reverse=True
        )

        # Top 3 concentration
        top_3_value = sum(float(p.current_value) for p in sorted_positions[:3])
        top_3_weight = round((top_3_value / total_value) * 100, 2)

        # Single asset max concentration
        max_single_asset = round((float(sorted_positions[0].current_value) / total_value) * 100, 2) if sorted_positions else 0.0

        # Single sector max concentration
        max_sector_pct = max(
            (sector["percentage"] for sector in sector_allocation.values()),
            default=0.0
        )

        return {
            "top_3_weight": top_3_weight,
            "single_sector_max": round(max_sector_pct, 2),
            "single_asset_max": max_single_asset
        }

    async def _get_position_rank(self, symbol: str) -> Dict[str, Any]:
        """
        Get position's rank in portfolio by value.

        Args:
            symbol: Asset symbol

        Returns:
            Dictionary with rank, total_positions, weight, description
        """
        positions = await self.portfolio_service.get_all_positions()
        valid_positions = [p for p in positions if p.current_value is not None]

        if not valid_positions:
            return {
                "rank": 0,
                "total_positions": 0,
                "weight": 0.0,
                "description": "No positions"
            }

        # Sort by value
        sorted_positions = sorted(
            valid_positions,
            key=lambda p: float(p.current_value),
            reverse=True
        )

        # Find position rank
        rank = 0
        for i, pos in enumerate(sorted_positions):
            if pos.symbol == symbol:
                rank = i + 1
                break

        total_value = sum(float(p.current_value) for p in valid_positions)
        position_value = next((float(p.current_value) for p in valid_positions if p.symbol == symbol), 0)
        weight = round((position_value / total_value * 100), 2) if total_value > 0 else 0.0

        # Format ordinal
        ordinal = self._format_ordinal(rank)

        return {
            "rank": rank,
            "total_positions": len(valid_positions),
            "weight": weight,
            "description": f"{ordinal} largest position ({weight}% of portfolio)"
        }

    def _format_ordinal(self, n: int) -> str:
        """Format number as ordinal (1st, 2nd, 3rd, etc.)."""
        if n == 0:
            return "0th"

        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
        if 11 <= (n % 100) <= 13:
            suffix = 'th'
        return f"{n}{suffix}"

    def _format_portfolio_context(self, context: Dict[str, Any]) -> str:
        """
        Format portfolio context as human-readable string for Claude prompt.

        Args:
            context: Portfolio context dictionary

        Returns:
            Formatted multi-line string
        """
        lines = [
            f"Total Portfolio Value: €{context['total_value']:,.2f}",
            f"Number of Positions: {context['position_count']}"
        ]

        # Asset allocation
        if context['asset_allocation']:
            lines.append("\nAsset Allocation:")
            for asset_type, data in context['asset_allocation'].items():
                lines.append(
                    f"  - {asset_type}: {data['percentage']:.1f}% (€{data['value']:,.2f}, {data['count']} positions)"
                )

        # Sector allocation
        if context['sector_allocation']:
            lines.append("\nSector Allocation (Stocks):")
            for sector, data in context['sector_allocation'].items():
                lines.append(
                    f"  - {sector}: {data['percentage']:.1f}% (€{data['value']:,.2f}, {data['count']} positions)"
                )

        # Top holdings
        if context['top_10_holdings']:
            lines.append("\nTop 10 Holdings:")
            for i, holding in enumerate(context['top_10_holdings'], 1):
                sector_info = f", {holding['sector']}" if 'sector' in holding else ""
                lines.append(
                    f"  {i}. {holding['symbol']}: €{holding['value']:,.2f} ({holding['weight']:.1f}%, {holding['asset_type']}{sector_info})"
                )

        # Concentration metrics
        lines.append("\nConcentration Metrics:")
        concentration = context['concentration_metrics']
        lines.append(f"  - Top 3 positions: {concentration['top_3_weight']:.1f}%")
        lines.append(f"  - Max single sector: {concentration['single_sector_max']:.1f}%")
        lines.append(f"  - Max single asset: {concentration['single_asset_max']:.1f}%")

        return "\n".join(lines)

    async def collect_strategy_analysis_data(
        self,
        strategy,  # InvestmentStrategy
        positions: list  # List[Position]
    ) -> Dict[str, Any]:
        """
        Collect data for strategy-driven portfolio analysis.

        Aggregates portfolio data, position details, and concentration metrics
        to enable AI-powered recommendations aligned with investment strategy.

        Args:
            strategy: InvestmentStrategy object with user's goals
            positions: List of Position objects

        Returns:
            Dictionary with strategy parameters, portfolio metrics, position
            details, asset/sector allocation, and concentration risk metrics
        """
        # Extract strategy parameters (handle None values)
        strategy_data = {
            "strategy_text": strategy.strategy_text,
            "target_annual_return": f"{float(strategy.target_annual_return):.2f}" if strategy.target_annual_return else "Not specified",
            "risk_tolerance": strategy.risk_tolerance or "Not specified",
            "time_horizon_years": str(strategy.time_horizon_years) if strategy.time_horizon_years else "Not specified",
            "max_positions": str(strategy.max_positions) if strategy.max_positions else "Not specified",
            "profit_taking_threshold": f"{float(strategy.profit_taking_threshold):.2f}" if strategy.profit_taking_threshold else "Not specified"
        }

        # Handle empty positions
        if not positions:
            return {
                **strategy_data,
                "portfolio_total_value": "0.00",
                "position_count": 0,
                "positions_table": "No positions",
                "asset_allocation": "No positions",
                "sector_allocation": "Not available",
                "geographic_exposure": "Not available",
                "top_3_weight": "0.00",
                "single_asset_max": "0.00",
                "single_sector_max": "0.00"
            }

        # Calculate portfolio totals
        valid_positions = [p for p in positions if p.current_value is not None]
        total_value = sum(float(p.current_value) for p in valid_positions)

        # Build positions detail table
        positions_table = self._build_positions_table(valid_positions, total_value)

        # Calculate asset allocation
        asset_allocation_dict = self._calculate_asset_allocation(valid_positions, total_value)
        asset_allocation_str = self._format_asset_allocation(asset_allocation_dict)

        # Calculate sector allocation (stocks only)
        sector_allocation_dict = self._calculate_sector_allocation(valid_positions, total_value)
        sector_allocation_str = self._format_sector_allocation(sector_allocation_dict)

        # Calculate concentration metrics
        concentration = self._calculate_concentration_metrics(
            valid_positions,
            total_value,
            sector_allocation_dict
        )

        # Geographic exposure (MVP: not available)
        geographic_exposure = "Not available"

        return {
            **strategy_data,
            "portfolio_total_value": f"{total_value:.2f}",
            "position_count": len(positions),
            "positions_table": positions_table,
            "asset_allocation": asset_allocation_str,
            "sector_allocation": sector_allocation_str,
            "geographic_exposure": geographic_exposure,
            "top_3_weight": f"{concentration['top_3_weight']:.2f}",
            "single_asset_max": f"{concentration['single_asset_max']:.2f}",
            "single_sector_max": f"{concentration['single_sector_max']:.2f}"
        }

    def _build_positions_table(self, positions: list, total_value: float) -> str:
        """
        Build markdown table of position details.

        Args:
            positions: List of Position objects
            total_value: Total portfolio value

        Returns:
            Markdown-formatted table string
        """
        if not positions:
            return "No positions"

        # Sort positions by value (descending) using existing helper
        sorted_positions = sorted(
            positions,
            key=lambda p: float(p.current_value) if p.current_value else 0,
            reverse=True
        )

        # Build table header
        lines = [
            "| Symbol | Asset Type | Quantity | Entry Price | Current Price | Value | P&L | P&L % | Holding Period |",
            "|--------|-----------|----------|-------------|---------------|-------|-----|-------|----------------|"
        ]

        # Build table rows
        for position in sorted_positions:
            # Calculate holding period
            holding_days = 0
            if position.first_purchase_date:
                # Handle both timezone-aware and naive datetimes
                now = datetime.now(UTC) if position.first_purchase_date.tzinfo else datetime.utcnow()
                holding_days = (now - position.first_purchase_date).days

            # Format values
            symbol = position.symbol
            asset_type = position.asset_type.value if isinstance(position.asset_type, AssetType) else str(position.asset_type)
            quantity = f"{float(position.quantity):.4f}" if position.quantity else "0"
            entry_price = f"€{float(position.avg_cost_basis):.2f}" if position.avg_cost_basis else "€0.00"
            current_price = f"€{float(position.current_price):.2f}" if position.current_price else "€0.00"
            value = f"€{float(position.current_value):,.2f}" if position.current_value else "€0.00"
            pnl = f"€{float(position.unrealized_pnl):,.2f}" if position.unrealized_pnl else "€0.00"
            pnl_pct = f"{float(position.unrealized_pnl_percent):.2f}%" if position.unrealized_pnl_percent else "0.00%"
            holding_period = f"{holding_days} days"

            row = f"| {symbol} | {asset_type} | {quantity} | {entry_price} | {current_price} | {value} | {pnl} | {pnl_pct} | {holding_period} |"
            lines.append(row)

        return "\n".join(lines)

    def _format_asset_allocation(self, allocation: Dict[str, Any]) -> str:
        """
        Format asset allocation dictionary as readable string.

        Args:
            allocation: Asset allocation dictionary from _calculate_asset_allocation

        Returns:
            Formatted string like "Stocks: 55% (€27,500), Crypto: 35% (€17,500)"
        """
        if not allocation:
            return "No asset allocation data"

        parts = []
        for asset_type, data in allocation.items():
            parts.append(
                f"{asset_type}: {data['percentage']:.1f}% (€{data['value']:,.2f})"
            )

        return ", ".join(parts)

    def _format_sector_allocation(self, allocation: Dict[str, Any]) -> str:
        """
        Format sector allocation dictionary as readable string.

        Args:
            allocation: Sector allocation dictionary from _calculate_sector_allocation

        Returns:
            Formatted string like "Technology: 75%, Finance: 20%, Consumer: 5%"
        """
        if not allocation:
            return "Not available"

        parts = []
        for sector, data in allocation.items():
            parts.append(f"{sector}: {data['percentage']:.1f}%")

        return ", ".join(parts)
