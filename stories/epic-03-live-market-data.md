# Epic 3: Live Market Data Integration

## Epic Overview
**Epic ID**: EPIC-03
**Epic Name**: Live Market Data Integration
**Epic Description**: Integrate real-time price feeds from Yahoo Finance with Redis caching
**Business Value**: Keep portfolio valuation current without manual price updates
**User Impact**: See portfolio value change in real-time during market hours
**Success Metrics**: Price updates within 60 seconds, handle API failures gracefully
**Status**: 🔴 Not Started

## Features in this Epic
- Feature 3.1: Yahoo Finance Integration
- Feature 3.2: Redis Cache Implementation
- Feature 3.3: Price Update Mechanism

## Progress Tracking
| Feature | Stories | Points | Status | Progress |
|---------|---------|--------|--------|----------|
| F3.1: Yahoo Finance Integration | 2 | 8 | 🔴 Not Started | 0% |
| F3.2: Redis Cache | 1 | 3 | 🔴 Not Started | 0% |
| F3.3: Price Updates | 1 | 5 | 🔴 Not Started | 0% |
| **Total** | **4** | **16** | **Not Started** | **0%** |

---

## Feature 3.1: Yahoo Finance Integration
**Feature Description**: Connect to Yahoo Finance API for real-time stock and crypto prices
**User Value**: Always see current market prices for accurate portfolio valuation
**Priority**: High
**Complexity**: 8 story points

### Story F3.1-001: Fetch Live Stock Prices
**Status**: 🔴 Not Started
**User Story**: As FX, I want real-time stock prices so that my portfolio value is always current

**Acceptance Criteria**:
- **Given** a list of stock tickers in my portfolio
- **When** fetching live prices
- **Then** current market prices are retrieved
- **And** bid/ask spread is available when market is open
- **And** last close price is used when market is closed
- **And** prices update every 60 seconds during market hours
- **And** after-hours prices are available when applicable
- **And** API failures are handled gracefully with exponential backoff

**Technical Requirements**:
- yfinance library integration
- Batch API calls for efficiency
- Market hours detection
- Error handling and retry logic
- Rate limiting compliance

**Implementation Design**:
```python
class YahooFinanceService:
    def __init__(self):
        self.rate_limiter = RateLimiter(max_calls=100, period=60)
        self.retry_policy = ExponentialBackoff(max_retries=3)

    def get_stock_prices(self, tickers: List[str]) -> Dict[str, PriceData]:
        # Batch fetch prices for multiple tickers
        # Handle market hours vs after-hours
        # Return price data with metadata

    def get_quote(self, ticker: str) -> Quote:
        # Get detailed quote including bid/ask

    def is_market_open(self) -> bool:
        # Check if US markets are open
```

**Price Data Structure**:
```python
class PriceData:
    ticker: str
    current_price: Decimal
    previous_close: Decimal
    day_change: Decimal
    day_change_percent: Decimal
    volume: int
    bid: Optional[Decimal]
    ask: Optional[Decimal]
    last_updated: datetime
    market_state: str  # 'open', 'closed', 'pre', 'post'
```

**Definition of Done**:
- [ ] yfinance integration implemented
- [ ] Batch price fetching for efficiency
- [ ] Market hours detection logic
- [ ] Error handling and retry logic
- [ ] Rate limiting implementation
- [ ] Logging for debugging
- [ ] Unit tests with mock data
- [ ] Integration tests with live API
- [ ] Performance: Fetch 50 tickers in <2 seconds

**Story Points**: 5
**Priority**: Must Have
**Dependencies**: F2.2-001 (Current Holdings)
**Risk Level**: Medium
**Assigned To**: Unassigned

**Error Handling Matrix**:
| Error Type | Response | User Impact |
|------------|----------|-------------|
| API Timeout | Retry with backoff | Use cached price |
| Rate Limit | Queue and delay | Temporary stale prices |
| Invalid Ticker | Log and skip | Show as "N/A" |
| Network Error | Use cache | Warning banner |

---

### Story F3.1-002: Fetch Cryptocurrency Prices
**Status**: 🔴 Not Started
**User Story**: As FX, I want real-time crypto prices so that I can track my Bitcoin and Ethereum investments

**Acceptance Criteria**:
- **Given** cryptocurrency holdings (BTC, ETH, etc.)
- **When** fetching crypto prices
- **Then** current prices are retrieved in USD
- **And** 24/7 price updates are supported
- **And** proper ticker format is used (BTC-USD, ETH-USD)
- **And** 24h change percentage is included
- **And** major cryptocurrencies are supported (top 20 by market cap)

**Technical Requirements**:
- Crypto ticker format conversion
- 24/7 update schedule
- USD pair fetching
- Support for major cryptocurrencies

**Supported Cryptocurrencies**:
```python
CRYPTO_MAPPINGS = {
    'BTC': 'BTC-USD',
    'ETH': 'ETH-USD',
    'ADA': 'ADA-USD',
    'DOT': 'DOT-USD',
    'LINK': 'LINK-USD',
    # ... top 20 cryptocurrencies
}

def normalize_crypto_ticker(symbol: str) -> str:
    # Convert Revolut format to Yahoo format
    # Handle various naming conventions
```

**Definition of Done**:
- [ ] Crypto price fetching implemented
- [ ] Ticker format conversion logic
- [ ] 24/7 update schedule configured
- [ ] Support for top 20 cryptocurrencies
- [ ] 24h statistics included
- [ ] Integration tests with live API
- [ ] Handle unlisted cryptocurrencies

**Story Points**: 3
**Priority**: Must Have
**Dependencies**: F3.1-001 (Stock Prices)
**Risk Level**: Low
**Assigned To**: Unassigned

---

## Feature 3.2: Redis Cache Implementation
**Feature Description**: Cache price data in Redis for performance and reliability
**User Value**: Fast response times and resilience to API failures
**Priority**: High
**Complexity**: 3 story points

### Story F3.2-001: Cache Price Data
**Status**: 🔴 Not Started
**User Story**: As FX, I want price data cached so that the app responds quickly and reduces API calls

**Acceptance Criteria**:
- **Given** fetched price data from Yahoo Finance
- **When** storing in cache
- **Then** prices are cached with 1-minute TTL for active markets
- **And** 5-minute TTL for closed markets
- **And** cache keys are properly namespaced (price:ticker:AAPL)
- **And** expired data triggers fresh fetch
- **And** cache misses are handled gracefully
- **And** bulk operations are optimized

**Technical Requirements**:
- Redis connection pool
- Serialization for price objects
- TTL management
- Namespace strategy
- Bulk get/set operations

**Redis Cache Design**:
```python
class PriceCache:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.namespace = "price"
        self.default_ttl = 60  # seconds

    def set_price(self, ticker: str, price_data: PriceData):
        key = f"{self.namespace}:{ticker}"
        ttl = self._calculate_ttl(price_data.market_state)
        self.redis.setex(key, ttl, json.dumps(price_data))

    def get_price(self, ticker: str) -> Optional[PriceData]:
        key = f"{self.namespace}:{ticker}"
        data = self.redis.get(key)
        return PriceData.from_json(data) if data else None

    def mget_prices(self, tickers: List[str]) -> Dict[str, PriceData]:
        # Bulk fetch from cache
        pipeline = self.redis.pipeline()
        for ticker in tickers:
            pipeline.get(f"{self.namespace}:{ticker}")
        results = pipeline.execute()
```

**Cache Key Structure**:
```
price:ticker:AAPL -> {current_price, last_updated, ...}
price:crypto:BTC-USD -> {current_price, 24h_change, ...}
price:metadata:last_fetch -> timestamp
price:market:status -> open/closed
```

**Definition of Done**:
- [ ] Redis connection established
- [ ] Cache write/read operations implemented
- [ ] TTL configuration based on market state
- [ ] Namespace strategy implemented
- [ ] Bulk operations optimized
- [ ] Cache invalidation logic
- [ ] Cache hit/miss metrics
- [ ] Unit tests with mock Redis
- [ ] Performance testing

**Story Points**: 3
**Priority**: Must Have
**Dependencies**: F3.1-001 (Yahoo Finance Integration)
**Risk Level**: Low
**Assigned To**: Unassigned

---

## Feature 3.3: Price Update Mechanism
**Feature Description**: Automatic background price updates with configurable refresh rates
**User Value**: Always see current prices without manual intervention
**Priority**: Should Have
**Complexity**: 5 story points

### Story F3.3-001: Automatic Price Refresh
**Status**: 🔴 Not Started
**User Story**: As FX, I want prices to update automatically so that I always see current values without manual refresh

**Acceptance Criteria**:
- **Given** the dashboard is open
- **When** 60 seconds have passed
- **Then** prices are automatically refreshed
- **And** updates occur every 60 seconds during market hours
- **And** updates occur every 5 minutes when markets are closed
- **And** 24/7 updates for cryptocurrencies
- **And** updates can be paused/resumed by user
- **And** last update timestamp is displayed

**Technical Requirements**:
- Background task scheduler
- WebSocket or Server-Sent Events
- Market hours awareness
- Different schedules for stocks/crypto
- User controls for auto-refresh

**Update Scheduler Design**:
```python
class PriceUpdateScheduler:
    def __init__(self, price_service, cache_service):
        self.price_service = price_service
        self.cache = cache_service
        self.scheduler = BackgroundScheduler()
        self.update_intervals = {
            'market_open': 60,  # seconds
            'market_closed': 300,  # 5 minutes
            'crypto': 60  # always 60 seconds
        }

    def start(self):
        # Schedule stock updates based on market hours
        self.scheduler.add_job(
            self.update_stock_prices,
            'interval',
            seconds=self._get_interval('stocks')
        )

        # Schedule 24/7 crypto updates
        self.scheduler.add_job(
            self.update_crypto_prices,
            'interval',
            seconds=60
        )

    async def push_updates(self, websocket):
        # Push price updates to connected clients
```

**WebSocket Protocol**:
```javascript
// Client-side subscription
ws.send(JSON.stringify({
    action: 'subscribe',
    tickers: ['AAPL', 'TSLA', 'BTC-USD']
}));

// Server push format
{
    type: 'price_update',
    data: {
        'AAPL': { price: 150.25, change: 1.5 },
        'TSLA': { price: 245.60, change: -2.3 }
    },
    timestamp: '2024-01-15T10:30:00Z'
}
```

**Definition of Done**:
- [ ] Background scheduler implemented
- [ ] Market hours detection for scheduling
- [ ] WebSocket/SSE implementation
- [ ] Different update frequencies configured
- [ ] User toggle for auto-refresh
- [ ] Last update timestamp display
- [ ] Graceful degradation without WebSocket
- [ ] Frontend real-time updates
- [ ] Connection retry logic
- [ ] Unit tests for scheduler
- [ ] Integration tests for real-time updates

**Story Points**: 5
**Priority**: Should Have
**Dependencies**: F3.2-001 (Cache), F4.1-001 (Dashboard)
**Risk Level**: Medium
**Assigned To**: Unassigned

---

## Technical Design Notes

### Price Fetching Pipeline
```python
1. Scheduled Trigger: Background job fires
2. Ticker Collection: Get unique tickers from positions
3. Cache Check: Try to get prices from Redis
4. API Fetch: Get missing prices from Yahoo Finance
5. Cache Update: Store fresh prices in Redis
6. Broadcast: Push updates via WebSocket
7. UI Update: React components re-render
```

### Performance Optimization
- Batch API requests (up to 50 tickers per call)
- Differential updates (only changed prices)
- Connection pooling for Redis
- Async/await for non-blocking operations
- CDN for static price history

### Reliability Measures
- Circuit breaker for API failures
- Fallback to cached prices
- Health check endpoint
- Monitoring and alerting
- Graceful degradation

---

## Dependencies
- **External**: Portfolio positions from Epic 2, Dashboard from Epic 4
- **Internal**: Yahoo Finance must work before caching
- **Libraries**: yfinance, redis-py, asyncio, apscheduler

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|---------|------------|
| Yahoo Finance API changes | No price updates | Abstract API layer, multiple providers |
| Rate limiting | Delayed updates | Caching, batch requests, backoff |
| Redis failure | Slow performance | Fallback to direct API calls |
| WebSocket connection issues | No real-time updates | Fallback to polling, auto-reconnect |

## Testing Strategy

**⚠️ MANDATORY TESTING REQUIREMENT**:
- **Minimum Coverage Threshold**: 85% code coverage for all modules
- **No story is complete without passing tests meeting this threshold**

1. **Unit Tests** (Required - 85% minimum coverage): Mock API responses and Redis
2. **Integration Tests** (Required): Live API with test tickers
3. **Load Tests**: 100+ tickers simultaneously
4. **Failure Tests**: API down, Redis down scenarios
5. **Real-time Tests**: WebSocket update latency

## Performance Requirements
- Fetch 50 tickers in <2 seconds
- Cache hit ratio >90% during trading hours
- WebSocket latency <100ms
- Support 100+ concurrent dashboard users

## Definition of Done for Epic
- [ ] All 4 stories completed
- [ ] Yahoo Finance integration working for stocks and crypto
- [ ] Redis caching with appropriate TTLs
- [ ] Automatic price updates on schedule
- [ ] Real-time updates to frontend
- [ ] Graceful handling of API failures
- [ ] Performance meets requirements
- [ ] Unit test coverage ≥85% (mandatory threshold)
- [ ] Documentation includes API limits and caching strategy