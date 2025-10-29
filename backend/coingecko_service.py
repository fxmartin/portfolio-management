# ABOUTME: CoinGecko API integration for cryptocurrency fundamental data
# ABOUTME: Provides ATH/ATL, market cap, supply metrics, and market rankings

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Optional
from dataclasses import dataclass
import aiohttp
import json


@dataclass
class CoinGeckoFundamentals:
    """Cryptocurrency fundamental data from CoinGecko"""
    symbol: str
    coin_id: str
    name: str
    current_price: Decimal
    market_cap: int
    market_cap_rank: Optional[int]
    total_volume_24h: int
    circulating_supply: Optional[Decimal]
    max_supply: Optional[Decimal]
    ath: Decimal
    ath_date: datetime
    ath_change_percentage: Decimal
    atl: Decimal
    atl_date: datetime
    atl_change_percentage: Decimal
    price_change_24h: Decimal
    price_change_percentage_24h: Decimal
    price_change_percentage_7d: Optional[Decimal]
    price_change_percentage_30d: Optional[Decimal]
    price_change_percentage_1y: Optional[Decimal]
    all_time_high_roi: Optional[Decimal]  # ROI from ATL to ATH


@dataclass
class GlobalCryptoMarketData:
    """Global cryptocurrency market data from CoinGecko"""
    total_market_cap_eur: int
    total_volume_24h_eur: int
    btc_dominance: Decimal  # Bitcoin market cap as % of total
    eth_dominance: Decimal  # Ethereum market cap as % of total
    active_cryptocurrencies: int
    markets: int  # Number of exchanges/markets
    market_cap_change_24h: Decimal  # Percentage change
    # DeFi metrics
    defi_market_cap_eur: Optional[int]
    defi_dominance: Optional[Decimal]  # DeFi as % of total market cap
    defi_24h_volume_eur: Optional[int]
    # Fear & Greed
    fear_greed_value: Optional[int]  # 0-100 (0 = Extreme Fear, 100 = Extreme Greed)
    fear_greed_classification: Optional[str]  # "Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"


class CoinGeckoRateLimiter:
    """Rate limiter for CoinGecko API (50 calls/minute free tier)"""

    def __init__(self, calls_per_minute: int = 50):
        """
        Initialize rate limiter

        Args:
            calls_per_minute: Maximum API calls per minute (default: 50 for free tier)
        """
        self.calls_per_minute = calls_per_minute
        self.tokens = calls_per_minute
        self.last_refill = datetime.now()

    async def acquire(self):
        """Acquire a token from the rate limiter. Blocks if limit reached."""
        now = datetime.now()

        # Refill if 60+ seconds have passed
        if (now - self.last_refill).total_seconds() >= 60:
            self.tokens = self.calls_per_minute
            self.last_refill = now

        # Wait if no tokens available
        if self.tokens <= 0:
            wait_seconds = 60 - (now - self.last_refill).total_seconds()
            if wait_seconds > 0:
                print(f"[CoinGecko] Rate limit: waiting {wait_seconds:.1f}s for refill")
                await asyncio.sleep(wait_seconds)
                return await self.acquire()

        self.tokens -= 1


class CoinGeckoService:
    """Service for fetching cryptocurrency fundamentals from CoinGecko API"""

    # Free tier uses api.coingecko.com, Pro/Demo tiers use pro-api.coingecko.com
    FREE_API_URL = "https://api.coingecko.com/api/v3"
    PRO_API_URL = "https://pro-api.coingecko.com/api/v3"

    # Symbol to CoinGecko ID mappings
    # CoinGecko uses different identifiers than ticker symbols
    SYMBOL_TO_ID = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'SOL': 'solana',
        'ADA': 'cardano',
        'DOT': 'polkadot',
        'MATIC': 'matic-network',
        'AVAX': 'avalanche-2',
        'LINK': 'chainlink',
        'UNI': 'uniswap',
        'ATOM': 'cosmos',
        'XRP': 'ripple',
        'DOGE': 'dogecoin',
        'LTC': 'litecoin',
        'BCH': 'bitcoin-cash',
        'XLM': 'stellar',
        'ALGO': 'algorand',
        'VET': 'vechain',
        'FIL': 'filecoin',
        'AAVE': 'aave',
        'SUSHI': 'sushi',
        'CRV': 'curve-dao-token',
        'GRT': 'the-graph',
        'MANA': 'decentraland',
        'SAND': 'the-sandbox',
        'AXS': 'axie-infinity',
        'ENJ': 'enjincoin',
        'CHZ': 'chiliz',
        'ZIL': 'zilliqa',
        'CAKE': 'pancakeswap-token',
        'RUNE': 'thorchain',
    }

    def __init__(self, api_key: Optional[str] = None, redis_client=None, calls_per_minute: int = 30):
        """
        Initialize CoinGecko service

        Args:
            api_key: Optional CoinGecko API key (Demo tier or higher)
            redis_client: Optional Redis client for caching
            calls_per_minute: Rate limit (default: 30 for Demo tier)
        """
        self.api_key = api_key
        self.rate_limiter = CoinGeckoRateLimiter(calls_per_minute=calls_per_minute)
        self.redis_client = redis_client

        # Demo tier keys use the same URL as free tier (api.coingecko.com)
        # Only Pro tier keys (CG-Pro-...) use pro-api.coingecko.com
        self.base_url = self.PRO_API_URL if (api_key and api_key.startswith('CG-Pro-')) else self.FREE_API_URL

        # Cache TTL: 1 hour (fundamentals don't change frequently)
        self.cache_ttl = 3600

    def _get_coin_id(self, symbol: str) -> str:
        """
        Convert symbol to CoinGecko coin ID

        Args:
            symbol: Crypto ticker symbol (e.g., "BTC", "ETH")

        Returns:
            CoinGecko coin ID (e.g., "bitcoin", "ethereum")

        Raises:
            ValueError: If symbol not supported
        """
        coin_id = self.SYMBOL_TO_ID.get(symbol.upper())
        if not coin_id:
            raise ValueError(f"Unsupported cryptocurrency symbol: {symbol}")
        return coin_id

    async def get_fundamentals(self, symbol: str) -> CoinGeckoFundamentals:
        """
        Get comprehensive fundamental data for a cryptocurrency

        Args:
            symbol: Crypto ticker symbol (e.g., "BTC", "SOL")

        Returns:
            CoinGeckoFundamentals with all available data

        Raises:
            ValueError: If symbol not supported
            Exception: If API returns error or no data
        """
        coin_id = self._get_coin_id(symbol)
        cache_key = f"cg:fundamentals:{coin_id}"

        # Check cache first
        if self.redis_client:
            cached = await self.redis_client.get(cache_key)
            if cached:
                print(f"[CoinGecko] Cache HIT for {symbol}")
                # Redis returns bytes, decode if needed
                if isinstance(cached, bytes):
                    cached = cached.decode('utf-8')
                return self._deserialize_fundamentals(cached)

        # Acquire rate limit token
        await self.rate_limiter.acquire()

        print(f"[CoinGecko] Cache MISS - Fetching from API for {symbol}")

        # Build request params
        params = {
            'localization': 'false',  # Skip localized text (smaller response)
            'tickers': 'false',       # Skip ticker data (we don't need exchanges)
            'market_data': 'true',    # Include market data
            'community_data': 'false',
            'developer_data': 'false',
            'sparkline': 'false'
        }

        # For Pro API, use x-cg-pro-api-key header instead of query param
        headers = {}
        if self.api_key:
            headers['x-cg-pro-api-key'] = self.api_key

        # Fetch from API
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/coins/{coin_id}"
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 429:
                    raise Exception("CoinGecko rate limit exceeded")
                if response.status != 200:
                    text = await response.text()
                    raise Exception(f"CoinGecko API error {response.status}: {text}")

                data = await response.json()

        # Parse response
        market_data = data.get('market_data', {})

        if not market_data:
            raise Exception(f"No market data available for {symbol}")

        # Extract data with safe fallbacks
        fundamentals = CoinGeckoFundamentals(
            symbol=symbol.upper(),
            coin_id=coin_id,
            name=data.get('name', symbol),
            current_price=Decimal(str(market_data['current_price'].get('eur', 0))),
            market_cap=int(market_data.get('market_cap', {}).get('eur', 0)),
            market_cap_rank=market_data.get('market_cap_rank'),
            total_volume_24h=int(market_data.get('total_volume', {}).get('eur', 0)),
            circulating_supply=Decimal(str(market_data.get('circulating_supply', 0))) if market_data.get('circulating_supply') else None,
            max_supply=Decimal(str(market_data.get('max_supply', 0))) if market_data.get('max_supply') else None,
            ath=Decimal(str(market_data.get('ath', {}).get('eur', 0))),
            ath_date=datetime.fromisoformat(market_data.get('ath_date', {}).get('eur', '2020-01-01T00:00:00.000Z').replace('Z', '+00:00')),
            ath_change_percentage=Decimal(str(market_data.get('ath_change_percentage', {}).get('eur', 0))),
            atl=Decimal(str(market_data.get('atl', {}).get('eur', 0))),
            atl_date=datetime.fromisoformat(market_data.get('atl_date', {}).get('eur', '2020-01-01T00:00:00.000Z').replace('Z', '+00:00')),
            atl_change_percentage=Decimal(str(market_data.get('atl_change_percentage', {}).get('eur', 0))),
            price_change_24h=Decimal(str(market_data.get('price_change_24h_in_currency', {}).get('eur', 0))),
            price_change_percentage_24h=Decimal(str(market_data.get('price_change_percentage_24h', 0))),
            price_change_percentage_7d=Decimal(str(market_data.get('price_change_percentage_7d', 0))) if market_data.get('price_change_percentage_7d') else None,
            price_change_percentage_30d=Decimal(str(market_data.get('price_change_percentage_30d', 0))) if market_data.get('price_change_percentage_30d') else None,
            price_change_percentage_1y=Decimal(str(market_data.get('price_change_percentage_1y', 0))) if market_data.get('price_change_percentage_1y') else None,
            all_time_high_roi=None  # Calculate below
        )

        # Calculate all-time ROI (from ATL to ATH)
        if fundamentals.ath and fundamentals.atl and fundamentals.atl > 0:
            fundamentals.all_time_high_roi = ((fundamentals.ath - fundamentals.atl) / fundamentals.atl * 100)

        # Cache result
        if self.redis_client:
            await self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                self._serialize_fundamentals(fundamentals)
            )

        return fundamentals

    def _serialize_fundamentals(self, fundamentals: CoinGeckoFundamentals) -> str:
        """Serialize fundamentals to JSON for caching"""
        return json.dumps({
            'symbol': fundamentals.symbol,
            'coin_id': fundamentals.coin_id,
            'name': fundamentals.name,
            'current_price': str(fundamentals.current_price),
            'market_cap': fundamentals.market_cap,
            'market_cap_rank': fundamentals.market_cap_rank,
            'total_volume_24h': fundamentals.total_volume_24h,
            'circulating_supply': str(fundamentals.circulating_supply) if fundamentals.circulating_supply else None,
            'max_supply': str(fundamentals.max_supply) if fundamentals.max_supply else None,
            'ath': str(fundamentals.ath),
            'ath_date': fundamentals.ath_date.isoformat(),
            'ath_change_percentage': str(fundamentals.ath_change_percentage),
            'atl': str(fundamentals.atl),
            'atl_date': fundamentals.atl_date.isoformat(),
            'atl_change_percentage': str(fundamentals.atl_change_percentage),
            'price_change_24h': str(fundamentals.price_change_24h),
            'price_change_percentage_24h': str(fundamentals.price_change_percentage_24h),
            'price_change_percentage_7d': str(fundamentals.price_change_percentage_7d) if fundamentals.price_change_percentage_7d else None,
            'price_change_percentage_30d': str(fundamentals.price_change_percentage_30d) if fundamentals.price_change_percentage_30d else None,
            'price_change_percentage_1y': str(fundamentals.price_change_percentage_1y) if fundamentals.price_change_percentage_1y else None,
            'all_time_high_roi': str(fundamentals.all_time_high_roi) if fundamentals.all_time_high_roi else None,
        })

    def _deserialize_fundamentals(self, data: str) -> CoinGeckoFundamentals:
        """Deserialize fundamentals from JSON cache"""
        obj = json.loads(data)
        return CoinGeckoFundamentals(
            symbol=obj['symbol'],
            coin_id=obj['coin_id'],
            name=obj['name'],
            current_price=Decimal(obj['current_price']),
            market_cap=obj['market_cap'],
            market_cap_rank=obj['market_cap_rank'],
            total_volume_24h=obj['total_volume_24h'],
            circulating_supply=Decimal(obj['circulating_supply']) if obj.get('circulating_supply') else None,
            max_supply=Decimal(obj['max_supply']) if obj.get('max_supply') else None,
            ath=Decimal(obj['ath']),
            ath_date=datetime.fromisoformat(obj['ath_date']),
            ath_change_percentage=Decimal(obj['ath_change_percentage']),
            atl=Decimal(obj['atl']),
            atl_date=datetime.fromisoformat(obj['atl_date']),
            atl_change_percentage=Decimal(obj['atl_change_percentage']),
            price_change_24h=Decimal(obj['price_change_24h']),
            price_change_percentage_24h=Decimal(obj['price_change_percentage_24h']),
            price_change_percentage_7d=Decimal(obj['price_change_percentage_7d']) if obj.get('price_change_percentage_7d') else None,
            price_change_percentage_30d=Decimal(obj['price_change_percentage_30d']) if obj.get('price_change_percentage_30d') else None,
            price_change_percentage_1y=Decimal(obj['price_change_percentage_1y']) if obj.get('price_change_percentage_1y') else None,
            all_time_high_roi=Decimal(obj['all_time_high_roi']) if obj.get('all_time_high_roi') else None,
        )

    async def _get_fear_greed_index(self) -> tuple[Optional[int], Optional[str]]:
        """
        Fetch Fear & Greed Index from Alternative.me API (free, no key required)

        Returns:
            Tuple of (value, classification) or (None, None) if unavailable
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.alternative.me/fng/"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('data') and len(data['data']) > 0:
                            latest = data['data'][0]
                            value = int(latest.get('value', 0))
                            classification = latest.get('value_classification', 'Unknown')
                            print(f"[Fear & Greed] Fetched: {value}/100 ({classification})")
                            return value, classification
                    else:
                        print(f"[Fear & Greed] API returned status {response.status}")
        except Exception as e:
            print(f"[Fear & Greed] Failed to fetch index: {e}")

        print("[Fear & Greed] Returning None (no data available)")
        return None, None

    async def get_global_market_data(self) -> GlobalCryptoMarketData:
        """
        Get global cryptocurrency market data

        Returns:
            GlobalCryptoMarketData with market overview metrics

        Raises:
            Exception: If API returns error or no data
        """
        cache_key = "cg:global_market"

        # Check cache first (15-minute TTL for global data)
        if self.redis_client:
            cached = await self.redis_client.get(cache_key)
            if cached:
                print("[CoinGecko] Cache HIT for global market data")
                if isinstance(cached, bytes):
                    cached = cached.decode('utf-8')
                return self._deserialize_global_data(cached)

        # Acquire rate limit token
        await self.rate_limiter.acquire()

        print("[CoinGecko] Cache MISS - Fetching global market data from API")

        headers = {}
        if self.api_key:
            headers['x-cg-pro-api-key'] = self.api_key

        # Fetch global market data
        async with aiohttp.ClientSession() as session:
            # 1. Get general global data
            url = f"{self.base_url}/global"
            async with session.get(url, headers=headers) as response:
                if response.status == 429:
                    raise Exception("CoinGecko rate limit exceeded")
                if response.status != 200:
                    text = await response.text()
                    raise Exception(f"CoinGecko API error {response.status}: {text}")

                global_data = await response.json()

            # 2. Get DeFi data (separate endpoint)
            defi_market_cap = None
            defi_volume = None
            defi_dominance = None

            try:
                await self.rate_limiter.acquire()
                url = f"{self.base_url}/global/decentralized_finance_defi"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        defi_data = await response.json()
                        defi_stats = defi_data.get('data', {})
                        defi_market_cap = int(defi_stats.get('defi_market_cap', 0))
                        defi_volume = int(defi_stats.get('trading_volume_24h', 0))
                        defi_dominance = Decimal(str(defi_stats.get('defi_dominance', 0)))
            except Exception as e:
                print(f"[CoinGecko] DeFi data fetch failed (non-critical): {e}")

        # Parse response
        data = global_data.get('data', {})
        if not data:
            raise Exception("No global market data available")

        # Extract market cap and volume in EUR
        market_caps = data.get('total_market_cap', {})
        volumes = data.get('total_volume', {})
        market_cap_percentages = data.get('market_cap_percentage', {})
        market_cap_change = data.get('market_cap_change_percentage_24h_usd', 0)

        # Fetch Fear & Greed Index (separate API, free tier)
        fear_greed_value, fear_greed_classification = await self._get_fear_greed_index()

        # Build result
        result = GlobalCryptoMarketData(
            total_market_cap_eur=int(market_caps.get('eur', 0)),
            total_volume_24h_eur=int(volumes.get('eur', 0)),
            btc_dominance=Decimal(str(market_cap_percentages.get('btc', 0))),
            eth_dominance=Decimal(str(market_cap_percentages.get('eth', 0))),
            active_cryptocurrencies=data.get('active_cryptocurrencies', 0),
            markets=data.get('markets', 0),
            market_cap_change_24h=Decimal(str(market_cap_change)),
            defi_market_cap_eur=defi_market_cap,
            defi_dominance=defi_dominance,
            defi_24h_volume_eur=defi_volume,
            fear_greed_value=fear_greed_value,
            fear_greed_classification=fear_greed_classification
        )

        # Cache for 15 minutes
        if self.redis_client:
            await self.redis_client.setex(
                cache_key,
                900,  # 15 minutes
                self._serialize_global_data(result)
            )

        return result

    def _serialize_global_data(self, data: GlobalCryptoMarketData) -> str:
        """Serialize global market data to JSON for caching"""
        return json.dumps({
            'total_market_cap_eur': data.total_market_cap_eur,
            'total_volume_24h_eur': data.total_volume_24h_eur,
            'btc_dominance': str(data.btc_dominance),
            'eth_dominance': str(data.eth_dominance),
            'active_cryptocurrencies': data.active_cryptocurrencies,
            'markets': data.markets,
            'market_cap_change_24h': str(data.market_cap_change_24h),
            'defi_market_cap_eur': data.defi_market_cap_eur,
            'defi_dominance': str(data.defi_dominance) if data.defi_dominance else None,
            'defi_24h_volume_eur': data.defi_24h_volume_eur,
            'fear_greed_value': data.fear_greed_value,
            'fear_greed_classification': data.fear_greed_classification
        })

    def _deserialize_global_data(self, data: str) -> GlobalCryptoMarketData:
        """Deserialize global market data from JSON cache"""
        obj = json.loads(data)
        return GlobalCryptoMarketData(
            total_market_cap_eur=obj['total_market_cap_eur'],
            total_volume_24h_eur=obj['total_volume_24h_eur'],
            btc_dominance=Decimal(obj['btc_dominance']),
            eth_dominance=Decimal(obj['eth_dominance']),
            active_cryptocurrencies=obj['active_cryptocurrencies'],
            markets=obj['markets'],
            market_cap_change_24h=Decimal(obj['market_cap_change_24h']),
            defi_market_cap_eur=obj.get('defi_market_cap_eur'),
            defi_dominance=Decimal(obj['defi_dominance']) if obj.get('defi_dominance') else None,
            defi_24h_volume_eur=obj.get('defi_24h_volume_eur'),
            fear_greed_value=obj.get('fear_greed_value'),
            fear_greed_classification=obj.get('fear_greed_classification')
        )
