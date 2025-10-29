# AI-Powered Market Analysis Documentation

## Overview

The AI Analysis system (Epic 8) integrates Anthropic's Claude AI to provide intelligent market insights, position-level recommendations, and two-quarter price forecasts. This document details the prompts, data flows, and response processing.

**Status**: ✅ Complete (65/65 story points, 181 tests passing)
**Model**: Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)
**API Provider**: Anthropic Messages API

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Prompt Templates](#prompt-templates)
3. [Data Collection](#data-collection)
4. [Claude API Integration](#claude-api-integration)
5. [Response Processing](#response-processing)
6. [Caching Strategy](#caching-strategy)
7. [Database Storage](#database-storage)
8. [Example Flows](#example-flows)

---

## System Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      React Frontend                          │
│  (GlobalAnalysisCard, PositionAnalysisList, ForecastPanel)  │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/REST
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                   Analysis Router                            │
│  GET /api/analysis/global                                    │
│  GET /api/analysis/position/{symbol}                         │
│  GET /api/analysis/forecast/{symbol}                         │
│  POST /api/analysis/positions/bulk                           │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                  Analysis Service                            │
│  • Orchestrates complete flow                                │
│  • Manages caching (Redis)                                   │
│  • Stores results (PostgreSQL)                               │
└─────┬───────────────────────┬───────────────────┬───────────┘
      │                       │                   │
      ↓                       ↓                   ↓
┌──────────────┐    ┌────────────────┐    ┌───────────────┐
│   Prompt     │    │ Data Collector │    │ Claude Service│
│   Service    │    │  (Portfolio,   │    │  (Anthropic  │
│  (Database)  │    │  Yahoo Finance)│    │   API Calls) │
└──────────────┘    └────────────────┘    └───────────────┘
```

### Service Responsibilities

1. **Analysis Router** (`analysis_router.py`)
   - FastAPI endpoints for analysis requests
   - Request validation (Pydantic schemas)
   - Response formatting

2. **Analysis Service** (`analysis_service.py`)
   - Orchestrates prompt → data → Claude → response flow
   - Cache checking and invalidation
   - Database storage of results

3. **Prompt Service** (`prompt_service.py`)
   - CRUD operations for prompt templates
   - Version management
   - Retrieval by name/category

4. **Prompt Renderer** (`prompt_renderer.py`)
   - Template variable substitution
   - Type-safe formatting (decimal, integer, array, object)
   - Data collection from portfolio and market APIs

5. **Claude Service** (`claude_service.py`)
   - Anthropic API client
   - Rate limiting (50 req/min)
   - Retry logic with exponential backoff
   - Token tracking

---

## Prompt Templates

Three default prompts are seeded on database initialization (`seed_prompts.py`):

### 1. Global Market Analysis

**Name**: `global_market_analysis`
**Category**: `global`
**Purpose**: Portfolio-wide market insights

**Template Variables**:
- `portfolio_value` (decimal) - Total portfolio value in EUR
- `asset_allocation` (object) - Breakdown by asset type with percentages
- `position_count` (integer) - Number of open positions
- `top_holdings` (array) - List of top 10 holdings with values

**Prompt Text**:
```
You are a professional financial analyst providing market insights for a portfolio management application.

Current Portfolio Context:
- Total Value: {portfolio_value}
- Asset Allocation: {asset_allocation}
- Open Positions: {position_count}
- Top Holdings: {top_holdings}

Provide a succinct market analysis (200-300 words) covering:
1. Current market sentiment and key trends
2. Macro-economic factors affecting this portfolio
3. Sector-specific insights relevant to holdings
4. Risk factors to monitor

Be direct, data-driven, and actionable. Focus on what matters for this specific portfolio mix.
```

**Example Rendered Prompt**:
```
You are a professional financial analyst providing market insights for a portfolio management application.

Current Portfolio Context:
- Total Value: €25,847.33
- Asset Allocation: Stocks: 48.2% (€12,458.50), Crypto: 35.8% (€9,253.40), Metals: 16.0% (€4,135.43)
- Open Positions: 14
- Top Holdings: MSTR (€4,890.44), AMEM (€6,612.62), BTC (€3,245.20), SOL (€2,850.33), ETH (€1,987.65)

Provide a succinct market analysis (200-300 words) covering:
1. Current market sentiment and key trends
2. Macro-economic factors affecting this portfolio
3. Sector-specific insights relevant to holdings
4. Risk factors to monitor

Be direct, data-driven, and actionable. Focus on what matters for this specific portfolio mix.
```

---

### 2. Position-Specific Analysis

**Name**: `position_analysis`
**Category**: `position`
**Purpose**: Individual asset recommendations

**Template Variables**:
- `symbol` (string) - Asset ticker
- `name` (string) - Full asset name
- `quantity` (decimal) - Number of shares/units held
- `current_price` (decimal) - Latest market price
- `cost_basis` (decimal) - FIFO-calculated average cost
- `unrealized_pnl` (decimal) - Unrealized profit/loss
- `pnl_percentage` (decimal) - P&L as percentage
- `position_percentage` (decimal) - Position size as % of portfolio
- `day_change` (decimal) - 24-hour price change %
- `sector` (string) - Sector/industry classification
- `asset_type` (string) - STOCKS, CRYPTO, or METALS

**Prompt Text**:
```
Analyze the following investment position for a personal portfolio:

Asset: {symbol} ({name})
Current Holdings: {quantity} shares/units
Current Price: {current_price}
Cost Basis: {cost_basis}
Unrealized P&L: {unrealized_pnl} ({pnl_percentage}%)
Position Size: {position_percentage}% of portfolio

Market Context:
- 24h Change: {day_change}%
- Sector: {sector}
- Asset Type: {asset_type}

Provide analysis (150-200 words) covering:
1. Current market position and recent performance
2. Key factors driving price movement
3. Risk assessment for this holding
4. Recommended action: HOLD, BUY_MORE, REDUCE, or SELL (with brief rationale)

Be concise and actionable.
```

**Example Rendered Prompt**:
```
Analyze the following investment position for a personal portfolio:

Asset: MSTR (MicroStrategy Incorporated)
Current Holdings: 19.68 shares/units
Current Price: €248.50
Cost Basis: €285.20
Unrealized P&L: -€723.44 (-12.77%)
Position Size: 18.9% of portfolio

Market Context:
- 24h Change: +3.42%
- Sector: Technology
- Asset Type: STOCKS

Provide analysis (150-200 words) covering:
1. Current market position and recent performance
2. Key factors driving price movement
3. Risk assessment for this holding
4. Recommended action: HOLD, BUY_MORE, REDUCE, or SELL (with brief rationale)

Be concise and actionable.
```

---

### 3. Two-Quarter Forecast

**Name**: `forecast_two_quarters`
**Category**: `forecast`
**Purpose**: Q1/Q2 price forecasts with scenarios

**Template Variables**:
- `symbol` (string) - Asset ticker
- `name` (string) - Full asset name
- `current_price` (decimal) - Latest market price
- `week_52_low` (decimal) - 52-week low price
- `week_52_high` (decimal) - 52-week high price
- `performance_30d` (decimal) - 30-day return %
- `performance_90d` (decimal) - 90-day return %
- `performance_180d` (decimal) - 180-day return %
- `performance_365d` (decimal) - 365-day return %
- `volatility_30d` (decimal) - 30-day annualized volatility
- `sector` (string) - Sector classification
- `asset_type` (string) - Asset type
- `market_context` (string) - Relevant market indices with changes
- `historical_prices` (string) - 365 days of historical price data

**Prompt Text**:
```
Generate a two-quarter price forecast for the following asset:

Asset: {symbol} ({name})
Current Price: {current_price}
52-Week Range: {week_52_low} - {week_52_high}
Recent Performance: {performance_30d} (30d), {performance_90d} (90d)
Sector: {sector}
Asset Type: {asset_type}

Market Context:
{market_context}

Provide a structured forecast for Q1 and Q2 (next 6 months) with:
1. **Pessimistic Scenario**: Conservative downside estimate
2. **Realistic Scenario**: Most likely outcome based on current trends
3. **Optimistic Scenario**: Upside potential with favorable conditions

For EACH scenario, provide:
- Target price at end of Q1 and Q2
- Confidence percentage (0-100%)
- Key assumptions driving the scenario
- Main risk factors

Format response as JSON:
{
  "q1_forecast": {
    "pessimistic": {"price": X, "confidence": Y, "assumptions": "...", "risks": "..."},
    "realistic": {"price": X, "confidence": Y, "assumptions": "...", "risks": "..."},
    "optimistic": {"price": X, "confidence": Y, "assumptions": "...", "risks": "..."}
  },
  "q2_forecast": { ... same structure ... },
  "overall_outlook": "Brief 2-3 sentence summary"
}
```

**Example Rendered Prompt**:
```
Generate a two-quarter price forecast for the following asset:

Asset: BTC (Bitcoin)
Current Price: €89,234.50
52-Week Range: €45,200.00 - €98,500.00
Recent Performance: +5.2% (30d), +18.7% (90d), +145.3% (365d)
Volatility (30d): 42.3%
Sector: Cryptocurrency
Asset Type: CRYPTO

Market Context:
S&P 500: +0.8% (24h)
Bitcoin: +2.3% (24h)
Gold: -0.2% (24h)

Historical Price Data (365 days):
[365 days of OHLC data formatted as CSV-style string]

Provide a structured forecast for Q1 and Q2 (next 6 months) with:
1. **Pessimistic Scenario**: Conservative downside estimate
2. **Realistic Scenario**: Most likely outcome based on current trends
3. **Optimistic Scenario**: Upside potential with favorable conditions

For EACH scenario, provide:
- Target price at end of Q1 and Q2
- Confidence percentage (0-100%)
- Key assumptions driving the scenario
- Main risk factors

Format response as JSON:
{ ... }
```

---

## Data Collection

### Global Analysis Data Collection

**Method**: `PromptDataCollector.collect_global_data()`

**Data Sources**:
1. **Portfolio Service** - Current positions, values, P&L
2. **Yahoo Finance Service** - Market indices (S&P 500, Dow, Bitcoin, Gold)

**Collected Fields** (10 total):
```python
{
    "portfolio_value": "25847.33",  # EUR, formatted to 2 decimals
    "position_count": "14",
    "asset_allocation": "Stocks: 48.2% (€12,458.50), Crypto: 35.8% (€9,253.40), Metals: 16.0% (€4,135.43)",
    "sector_allocation": "Stocks: 48.2%, Crypto: 35.8%, Metals: 16.0%",
    "market_indices": "S&P 500: 5,851.20 (+0.8%), Dow: 42,563.00 (+0.5%), Bitcoin: 89,234.50 (+2.3%), Gold: 2,678.40 (-0.2%)",
    "portfolio_performance": "Unrealized P&L: €2,345.67 (+9.98%)",
    "top_holdings": "MSTR (€4,890.44), AMEM (€6,612.62), BTC (€3,245.20), SOL (€2,850.33), ETH (€1,987.65), ...",
    "total_unrealized_pnl": "2345.67",
    "total_unrealized_pnl_percentage": "9.98",
    "open_position_count": "14"
}
```

**Process**:
1. Query all open positions from database
2. Calculate portfolio value (sum of position values)
3. Calculate asset allocation percentages
4. Fetch market indices from Yahoo Finance (with error handling)
5. Format top 10 holdings by value
6. Calculate aggregate P&L metrics

---

### Position Analysis Data Collection

**Method**: `PromptDataCollector.collect_position_data(symbol: str)`

**Data Sources**:
1. **Portfolio Service** - Position details (quantity, cost basis, P&L)
2. **Yahoo Finance Service** - Current price, 24h change
3. **Yahoo Finance API** (yfinance) - Fundamentals, sector, industry

**Collected Fields** (18 total):
```python
{
    # Basic Position Data
    "symbol": "MSTR",
    "name": "MicroStrategy Incorporated",
    "quantity": "19.68",
    "current_price": "248.50",
    "cost_basis": "285.20",
    "unrealized_pnl": "-723.44",
    "pnl_percentage": "-12.77",
    "position_percentage": "18.9",

    # Market Data
    "day_change": "3.42",
    "asset_type": "STOCKS",

    # Yahoo Finance Fundamentals
    "sector": "Technology",
    "industry": "Software - Application",
    "week_52_low": "198.50",
    "week_52_high": "543.00",
    "volume": "8234567",
    "market_cap": "42500000000",
    "pe_ratio": "N/A",

    # Transaction Context
    "transaction_count": "3",
    "first_purchase_date": "2024-11-15",
    "holding_period_days": "349"
}
```

**Process**:
1. Query position from database by symbol
2. Fetch current price from PriceHistory or Yahoo Finance
3. Calculate P&L and position percentage
4. Call `yfinance` API for stock fundamentals
5. Query transaction history for context
6. Handle missing data gracefully (return "N/A" or 0)

---

### Forecast Data Collection

**Method**: `PromptDataCollector.collect_forecast_data(symbol: str)`

**Data Sources**:
1. **Portfolio Service** - Basic position data
2. **Yahoo Finance Service** - Current price, 52-week range
3. **Yahoo Finance API** (yfinance) - 365 days historical OHLC data, fundamentals
4. **Market Indices** - Relevant benchmarks (S&P for stocks, BTC for crypto, Gold for metals)

**Collected Fields** (12 total):
```python
{
    # Basic Data
    "symbol": "BTC",
    "name": "Bitcoin",
    "current_price": "89234.50",
    "asset_type": "CRYPTO",
    "sector": "Cryptocurrency",

    # 52-Week Range
    "week_52_low": "45200.00",
    "week_52_high": "98500.00",

    # Performance Metrics (calculated from historical data)
    "performance_30d": "5.2",     # 30-day return %
    "performance_90d": "18.7",    # 90-day return %
    "performance_180d": "67.3",   # 180-day return %
    "performance_365d": "145.3",  # 365-day return %
    "volatility_30d": "42.3",     # 30-day annualized volatility

    # Market Context
    "market_context": "S&P 500: 5,851.20 (+0.8%), Bitcoin: 89,234.50 (+2.3%), Gold: 2,678.40 (-0.2%)",

    # Historical Data (365 days OHLC)
    "historical_prices": "Date,Open,High,Low,Close,Volume\n2024-10-29,89100.0,90500.0,88200.0,89234.5,42500\n..."
}
```

**Process**:
1. Query position from database
2. Fetch 365 days of historical price data from yfinance
3. Calculate performance metrics for 30d/90d/180d/365d periods
4. Calculate 30-day annualized volatility
5. Fetch relevant market indices based on asset type
6. Format historical data as CSV string (for Claude context)
7. Handle API errors gracefully (empty strings for missing data)

---

## Claude API Integration

### Configuration

**Environment Variables** (from `config.py`):
```python
ANTHROPIC_API_KEY: str          # sk-ant-... from console.anthropic.com
ANTHROPIC_MODEL: str            # "claude-sonnet-4-5-20250929"
ANTHROPIC_MAX_TOKENS: int       # 4096 (response length)
ANTHROPIC_TEMPERATURE: float    # 0.3 (deterministic)
ANTHROPIC_TIMEOUT: int          # 60 seconds
ANTHROPIC_MAX_RETRIES: int      # 3 attempts
ANTHROPIC_RATE_LIMIT: int       # 50 requests/minute
```

### Request Format

**Method**: `ClaudeService.generate_analysis(prompt: str)`

**Anthropic Messages API Call**:
```python
response = await client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    temperature=0.3,
    messages=[
        {
            "role": "user",
            "content": rendered_prompt  # From prompt template
        }
    ]
)
```

### Rate Limiting

**Strategy**: Token bucket with 50 requests/minute limit

**Implementation**:
```python
async def _check_rate_limit(self):
    """Enforce rate limit by delaying requests if needed."""
    now = time.time()

    # Remove requests older than 60 seconds
    while self.request_times and now - self.request_times[0] > 60:
        self.request_times.popleft()

    # If at limit, wait until oldest request is 60s old
    if len(self.request_times) >= self.rate_limit:
        oldest = self.request_times[0]
        wait_time = 60 - (now - oldest)
        if wait_time > 0:
            logger.warning(f"Rate limit reached, waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)

    self.request_times.append(now)
```

### Retry Logic

**Strategy**: Exponential backoff with 3 retries

**Backoff Delays**: 1s, 2s, 4s

**Retried Errors**:
- Network errors (ConnectionError, Timeout)
- Rate limit errors (429)
- Server errors (500, 502, 503)

**Implementation**:
```python
for attempt in range(self.max_retries):
    try:
        response = await self.client.messages.create(...)
        return response
    except (RateLimitError, ConnectionError, ServerError) as e:
        if attempt < self.max_retries - 1:
            delay = 2 ** attempt  # 1s, 2s, 4s
            logger.warning(f"Retry {attempt+1}/{self.max_retries} after {delay}s: {e}")
            await asyncio.sleep(delay)
        else:
            raise ClaudeAPIError(f"Failed after {self.max_retries} retries: {e}")
```

### Response Format

**Successful Response**:
```python
{
    'content': str,              # Analysis text or JSON (forecasts)
    'tokens_used': int,          # input_tokens + output_tokens
    'model': str,                # "claude-sonnet-4-5-20250929"
    'generation_time_ms': int,   # Time taken for API call
    'stop_reason': str           # "end_turn" | "max_tokens"
}
```

**Token Tracking**:
- Input tokens: Length of rendered prompt
- Output tokens: Length of Claude's response
- Total tokens: Sum of input + output (used for cost tracking)

---

## Response Processing

### Global Analysis

**Response Type**: Plain text (Markdown)

**Processing**:
1. No parsing required (raw markdown)
2. Store entire response in database
3. Return to frontend as-is
4. Frontend renders markdown with `react-markdown`

**Example Response**:
```markdown
## Market Sentiment

Current markets showing mixed signals with tech stocks under pressure while crypto rallies. Your portfolio's 48% allocation to stocks creates vulnerability to ongoing tech selloff.

## Macro Factors

Fed policy uncertainty continues to weigh on risk assets. Your MSTR position (19% of portfolio) faces dual exposure: tech sector weakness + Bitcoin correlation.

## Sector Insights

**Stocks**: ETFs (AMEM, MWOQ) provide diversification but European exposure adds FX risk.
**Crypto**: Bitcoin surge (+145% YoY) drives portfolio gains. Consider taking profits given concentration.
**Metals**: Metals position closed profitably (+28.7%) - smart tactical play.

## Risk Monitoring

1. MSTR concentration risk (19%) - largest position down 12.7%
2. Crypto volatility - 36% allocation to highly volatile assets
3. Currency risk - USD positions require EUR conversion
```

---

### Position Analysis

**Response Type**: Plain text with structured recommendation

**Processing**:
1. Store full text in database
2. Extract recommendation using regex
3. Validate recommendation against enum (HOLD, BUY_MORE, REDUCE, SELL)
4. Return both analysis text and parsed recommendation

**Extraction Logic**:
```python
def _extract_recommendation(analysis_text: str) -> Optional[Recommendation]:
    """Extract recommendation from Claude's response."""

    # Pattern matches: "Recommendation: HOLD" or "Action: BUY_MORE"
    pattern = r'(?:Recommendation|Recommended action|Action):\s*(\w+)'
    match = re.search(pattern, analysis_text, re.IGNORECASE)

    if match:
        action = match.group(1).upper()

        # Map variations to enum values
        mapping = {
            'HOLD': Recommendation.HOLD,
            'BUY': Recommendation.BUY_MORE,
            'BUY_MORE': Recommendation.BUY_MORE,
            'REDUCE': Recommendation.REDUCE,
            'SELL': Recommendation.SELL,
            'TRIM': Recommendation.REDUCE,
            'ACCUMULATE': Recommendation.BUY_MORE
        }

        return mapping.get(action)

    return None  # Could not extract
```

**Example Response**:
```markdown
## MicroStrategy (MSTR) Analysis

**Current Position**: Down 12.7% from your cost basis of €285.20. Recent 24h bounce of +3.4% shows some recovery momentum.

**Key Drivers**: MSTR trades as leveraged Bitcoin proxy. Bitcoin's recent surge (+145% YoY) should support price, but company's aggressive BTC accumulation strategy adds volatility. Q3 earnings showed operational losses offset by Bitcoin gains.

**Risk Assessment**: High concentration risk at 19% of portfolio. Dual exposure to software business fundamentals + Bitcoin price swings. Current valuation appears stretched relative to NAV.

**Recommendation: REDUCE**

Consider trimming position to 10-12% of portfolio. Take partial profits on recent bounce. Maintain core holding for Bitcoin exposure, but reduce concentration risk. Set stop-loss at €220 (-11% from current).
```

**Parsed Output**:
```python
{
    "analysis": "## MicroStrategy (MSTR) Analysis\n\n...",
    "recommendation": "REDUCE",
    "generated_at": "2025-10-29T15:42:33Z",
    "tokens_used": 892,
    "cached": False
}
```

---

### Forecast Analysis

**Response Type**: JSON with structured scenarios

**Processing**:
1. Extract JSON from response (may be wrapped in markdown code block)
2. Parse JSON and validate structure
3. Validate all required fields present
4. Store both raw response and parsed JSON
5. Return structured forecast data

**JSON Extraction**:
```python
def _extract_json_from_response(response_text: str) -> dict:
    """Extract JSON from Claude response (handles markdown code blocks)."""

    # Try direct JSON parse first
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block
    pattern = r'```(?:json)?\n(.*?)\n```'
    match = re.search(pattern, response_text, re.DOTALL)

    if match:
        json_str = match.group(1)
        return json.loads(json_str)

    raise InvalidResponseError("Could not extract JSON from response")
```

**Validation**:
```python
def _validate_forecast_structure(data: dict) -> bool:
    """Validate forecast JSON has all required fields."""

    required_keys = ['q1_forecast', 'q2_forecast', 'overall_outlook']
    if not all(k in data for k in required_keys):
        return False

    # Validate each quarter has 3 scenarios
    for quarter in ['q1_forecast', 'q2_forecast']:
        scenarios = data[quarter]
        required_scenarios = ['pessimistic', 'realistic', 'optimistic']

        if not all(s in scenarios for s in required_scenarios):
            return False

        # Validate each scenario has required fields
        for scenario in scenarios.values():
            required_fields = ['price', 'confidence', 'assumptions', 'risks']
            if not all(f in scenario for f in required_fields):
                return False

    return True
```

**Example Response**:
```json
{
  "q1_forecast": {
    "pessimistic": {
      "price": 75000.00,
      "confidence": 70,
      "assumptions": "Market correction, regulatory crackdown, macro headwinds",
      "risks": "Further downside if Fed hawkish, exchange failures, regulation"
    },
    "realistic": {
      "price": 95000.00,
      "confidence": 65,
      "assumptions": "Continued institutional adoption, stable macro, no major shocks",
      "risks": "Volatility remains high, regulatory uncertainty, market manipulation"
    },
    "optimistic": {
      "price": 120000.00,
      "confidence": 55,
      "assumptions": "ETF inflows surge, halving anticipation, favorable regulation",
      "risks": "Overheating, pullback after rapid gains, profit-taking"
    }
  },
  "q2_forecast": {
    "pessimistic": {
      "price": 65000.00,
      "confidence": 60,
      "assumptions": "Extended bear phase, recession fears, crypto winter",
      "risks": "Capitulation event, major exchange collapse, regulatory ban"
    },
    "realistic": {
      "price": 105000.00,
      "confidence": 60,
      "assumptions": "Post-halving strength, growing adoption, stable macro",
      "risks": "Halving sell-the-news event, summer doldrums, competition"
    },
    "optimistic": {
      "price": 150000.00,
      "confidence": 45,
      "assumptions": "New ATH, institutional FOMO, favorable policy, supply shock",
      "risks": "Bubble territory, unsustainable rally, sharp correction risk"
    }
  },
  "overall_outlook": "Bitcoin faces a critical juncture with the 2024 halving approaching. While long-term fundamentals remain strong (institutional adoption, scarcity), near-term volatility expected. Realistic target of €105K by Q2 assumes continued macro stability and post-halving strength."
}
```

---

## Caching Strategy

### Cache Implementation

**Technology**: Redis
**Library**: `redis-py` with async support

**Service**: `CacheService` (`cache_service.py`)

### TTL (Time-To-Live) Settings

| Analysis Type | TTL | Rationale |
|--------------|-----|-----------|
| Global Analysis | 1 hour (3600s) | Market conditions change frequently |
| Position Analysis | 1 hour (3600s) | Position data updates with price changes |
| Forecasts | 24 hours (86400s) | Long-term outlook changes slowly |

### Cache Keys

**Format**: `analysis:{type}:{identifier}`

**Examples**:
- `analysis:global` - Global market analysis
- `analysis:position:BTC` - Bitcoin position analysis
- `analysis:forecast:MSTR` - MSTR two-quarter forecast

### Cache Hit Flow

```python
async def get_cached_analysis(cache_key: str) -> Optional[Dict]:
    """
    Retrieve cached analysis if exists and not expired.

    Returns:
        Cached data or None if not found/expired
    """
    cached_json = await redis.get(cache_key)

    if not cached_json:
        return None

    return json.loads(cached_json)
```

### Cache Miss Flow

```python
async def set_cached_analysis(
    cache_key: str,
    data: Dict,
    ttl: int
) -> None:
    """
    Store analysis in cache with TTL.
    """
    await redis.setex(
        cache_key,
        ttl,
        json.dumps(data, default=str)  # Handle datetime serialization
    )
```

### Cache Invalidation

**Automatic Expiration**: TTL-based (no manual invalidation needed)

**Force Refresh**: All endpoints support `force_refresh=True` query parameter
```
GET /api/analysis/global?force_refresh=true
```

### Cache Performance

**Expected Hit Rates**:
- Global analysis: ~80% (1-hour cache, frequently accessed)
- Position analysis: ~60% (1-hour cache, accessed per-symbol)
- Forecasts: ~90% (24-hour cache, less frequently accessed)

**Benefit**: Reduces Claude API costs by ~75% in typical usage

---

## Database Storage

### Tables

Three tables store prompt and analysis data:

#### 1. `prompts`

**Purpose**: Store prompt templates and variables

```sql
CREATE TABLE prompts (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50) NOT NULL,
    prompt_text TEXT NOT NULL,
    template_variables JSON,
    is_active BOOLEAN DEFAULT TRUE,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Example Row**:
```json
{
    "id": 1,
    "name": "global_market_analysis",
    "category": "global",
    "prompt_text": "You are a professional financial analyst...",
    "template_variables": {
        "portfolio_value": "decimal",
        "asset_allocation": "object",
        "position_count": "integer",
        "top_holdings": "array"
    },
    "is_active": true,
    "version": 1,
    "created_at": "2025-10-25T10:00:00Z",
    "updated_at": "2025-10-25T10:00:00Z"
}
```

#### 2. `prompt_versions`

**Purpose**: Store historical versions of prompts (audit trail)

```sql
CREATE TABLE prompt_versions (
    id INTEGER PRIMARY KEY,
    prompt_id INTEGER REFERENCES prompts(id),
    version INTEGER NOT NULL,
    prompt_text TEXT NOT NULL,
    template_variables JSON,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Usage**: Automatically created when prompt is updated

#### 3. `analysis_results`

**Purpose**: Store AI-generated analyses with metadata

```sql
CREATE TABLE analysis_results (
    id INTEGER PRIMARY KEY,
    analysis_type VARCHAR(20) NOT NULL,  -- 'global', 'position', 'forecast'
    symbol VARCHAR(10),                  -- NULL for global, asset symbol for others
    prompt_id INTEGER REFERENCES prompts(id),
    prompt_version INTEGER,
    raw_response TEXT NOT NULL,          -- Full Claude response
    parsed_data JSON,                    -- Parsed recommendation/forecast (if applicable)
    tokens_used INTEGER NOT NULL,
    generation_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP                 -- For cleanup (1 hour for analysis, 24h for forecasts)
);

CREATE INDEX idx_analysis_type_symbol ON analysis_results(analysis_type, symbol, created_at);
CREATE INDEX idx_analysis_expires ON analysis_results(expires_at);
```

**Example Rows**:

**Global Analysis**:
```json
{
    "id": 1,
    "analysis_type": "global",
    "symbol": null,
    "prompt_id": 1,
    "prompt_version": 1,
    "raw_response": "## Market Sentiment\n\nCurrent markets showing...",
    "parsed_data": null,
    "tokens_used": 1523,
    "generation_time_ms": 2847,
    "created_at": "2025-10-29T15:30:00Z",
    "expires_at": "2025-10-29T16:30:00Z"
}
```

**Position Analysis**:
```json
{
    "id": 2,
    "analysis_type": "position",
    "symbol": "MSTR",
    "prompt_id": 2,
    "prompt_version": 1,
    "raw_response": "## MicroStrategy (MSTR) Analysis...",
    "parsed_data": {"recommendation": "REDUCE"},
    "tokens_used": 892,
    "generation_time_ms": 1956,
    "created_at": "2025-10-29T15:42:33Z",
    "expires_at": "2025-10-29T16:42:33Z"
}
```

**Forecast**:
```json
{
    "id": 3,
    "analysis_type": "forecast",
    "symbol": "BTC",
    "prompt_id": 3,
    "prompt_version": 1,
    "raw_response": "```json\n{\"q1_forecast\": {...}, ...}\n```",
    "parsed_data": {
        "q1_forecast": {
            "pessimistic": {"price": 75000, "confidence": 70, ...},
            "realistic": {"price": 95000, "confidence": 65, ...},
            "optimistic": {"price": 120000, "confidence": 55, ...}
        },
        "q2_forecast": {...},
        "overall_outlook": "..."
    },
    "tokens_used": 2145,
    "generation_time_ms": 3421,
    "created_at": "2025-10-29T16:00:00Z",
    "expires_at": "2025-10-30T16:00:00Z"
}
```

### Cleanup Strategy

**Automatic Cleanup**: Database cleanup job deletes expired analyses

```python
# Cleanup job (run daily via cron or scheduled task)
async def cleanup_expired_analyses():
    """Delete analysis results older than expires_at timestamp."""
    now = datetime.utcnow()

    deleted = await db.execute(
        delete(AnalysisResult)
        .where(AnalysisResult.expires_at < now)
    )

    logger.info(f"Cleaned up {deleted.rowcount} expired analyses")
```

**Retention**:
- Global/Position analyses: 1 hour (matches cache TTL)
- Forecasts: 24 hours (matches cache TTL)

---

## Example Flows

### Flow 1: Global Analysis Request

**User Action**: Opens Analysis page, clicks "Generate Analysis"

**Frontend**:
```typescript
const response = await fetch('/api/analysis/global');
const data = await response.json();
// { analysis: "...", generated_at: "...", tokens_used: 1523, cached: false }
```

**Backend Flow**:

1. **Router** (`GET /api/analysis/global`)
   ```python
   @router.get("/global")
   async def get_global_analysis(
       force_refresh: bool = False,
       service: AnalysisService = Depends(get_analysis_service)
   ):
       result = await service.generate_global_analysis(force_refresh)
       return GlobalAnalysisResponse(**result)
   ```

2. **Analysis Service**
   ```python
   async def generate_global_analysis(force_refresh: bool):
       # Check cache
       cache_key = "analysis:global"
       if not force_refresh:
           cached = await cache.get(cache_key)
           if cached:
               return {**cached, 'cached': True}

       # Fetch prompt
       prompt_template = await prompts.get_prompt_by_name("global_market_analysis")

       # Collect data
       data = await data_collector.collect_global_data()
       # Returns: {portfolio_value, asset_allocation, position_count, ...}

       # Render prompt
       renderer = PromptRenderer()
       rendered = renderer.render(
           prompt_template.prompt_text,
           prompt_template.template_variables,
           data
       )

       # Call Claude
       result = await claude.generate_analysis(rendered)
       # Returns: {content, tokens_used, generation_time_ms, ...}

       # Store in database
       analysis = AnalysisResult(
           analysis_type='global',
           symbol=None,
           prompt_id=prompt_template.id,
           raw_response=result['content'],
           tokens_used=result['tokens_used'],
           expires_at=datetime.utcnow() + timedelta(hours=1)
       )
       db.add(analysis)
       await db.commit()

       # Cache for 1 hour
       await cache.setex(cache_key, 3600, {
           'analysis': result['content'],
           'generated_at': datetime.utcnow(),
           'tokens_used': result['tokens_used']
       })

       return {
           'analysis': result['content'],
           'generated_at': datetime.utcnow(),
           'tokens_used': result['tokens_used'],
           'cached': False
       }
   ```

3. **Data Collector**
   ```python
   async def collect_global_data():
       # Get all positions
       positions = await portfolio_service.get_all_positions()

       # Calculate portfolio value
       portfolio_value = sum(p.current_value for p in positions)

       # Calculate asset allocation
       allocation = {}
       for p in positions:
           allocation[p.asset_type] = allocation.get(p.asset_type, 0) + p.current_value

       # Format allocation string
       allocation_str = ", ".join(
           f"{asset}: {(value/portfolio_value*100):.1f}% (€{value:.2f})"
           for asset, value in allocation.items()
       )

       # Get market indices
       indices = await yahoo_service.get_market_indices()

       # Format top holdings
       top_10 = sorted(positions, key=lambda p: p.current_value, reverse=True)[:10]
       holdings_str = ", ".join(f"{p.symbol} (€{p.current_value:.2f})" for p in top_10)

       return {
           'portfolio_value': f"{portfolio_value:.2f}",
           'position_count': str(len(positions)),
           'asset_allocation': allocation_str,
           'top_holdings': holdings_str,
           'market_indices': indices,
           # ... 5 more fields
       }
   ```

4. **Claude Service**
   ```python
   async def generate_analysis(prompt: str):
       # Rate limit check
       await self._check_rate_limit()

       # API call with retry
       for attempt in range(3):
           try:
               response = await self.client.messages.create(
                   model="claude-sonnet-4-5-20250929",
                   max_tokens=4096,
                   temperature=0.3,
                   messages=[{"role": "user", "content": prompt}]
               )

               return {
                   'content': response.content[0].text,
                   'tokens_used': response.usage.input_tokens + response.usage.output_tokens,
                   'generation_time_ms': ...,
                   'stop_reason': response.stop_reason
               }
           except RateLimitError:
               if attempt < 2:
                   await asyncio.sleep(2 ** attempt)
               else:
                   raise
   ```

**Total Time**: ~3-5 seconds (first request), ~50ms (cached)

**Token Usage**: ~1,500-2,000 tokens

**Cost**: $0.015-0.020 per request (Claude Sonnet 4.5 pricing)

---

### Flow 2: Position Analysis with Recommendation

**User Action**: Clicks "Analyze" button on Bitcoin position card

**Frontend**:
```typescript
const response = await fetch('/api/analysis/position/BTC');
const data = await response.json();
// { analysis: "...", recommendation: "HOLD", tokens_used: 892, cached: false }
```

**Key Differences from Global**:

1. **Symbol-specific cache key**: `analysis:position:BTC`
2. **Data collection**: Position-specific fundamentals from Yahoo Finance
3. **Recommendation extraction**: Parse recommendation from Claude's response
4. **Parsed data storage**: Store extracted recommendation in `parsed_data` column

**Recommendation Extraction**:
```python
# After Claude response
raw_response = result['content']

# Extract recommendation
recommendation = _extract_recommendation(raw_response)
# Uses regex to find "Recommendation: HOLD" in text

# Store both raw and parsed
analysis = AnalysisResult(
    analysis_type='position',
    symbol='BTC',
    raw_response=raw_response,
    parsed_data={'recommendation': recommendation.value} if recommendation else None,
    ...
)
```

---

### Flow 3: Forecast Generation

**User Action**: Clicks "View Forecast" on position card, selects Q1 tab

**Frontend**:
```typescript
const response = await fetch('/api/analysis/forecast/BTC');
const data = await response.json();
// { q1_forecast: {...}, q2_forecast: {...}, overall_outlook: "...", cached: false }
```

**Key Differences**:

1. **Historical data collection**: Fetch 365 days OHLC from yfinance
2. **Performance metrics calculation**: 30d/90d/180d/365d returns + volatility
3. **JSON response parsing**: Extract and validate structured forecast
4. **24-hour cache**: Longer TTL since forecasts change slowly

**Historical Price Fetching**:
```python
async def _get_historical_prices(symbol: str):
    """Fetch 365 days of historical price data."""
    ticker = yf.Ticker(symbol)

    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    # Fetch daily OHLC data
    hist = ticker.history(start=start_date, end=end_date)

    # Format as CSV string
    csv_lines = ["Date,Open,High,Low,Close,Volume"]
    for date, row in hist.iterrows():
        csv_lines.append(
            f"{date.strftime('%Y-%m-%d')},{row['Open']:.2f},"
            f"{row['High']:.2f},{row['Low']:.2f},"
            f"{row['Close']:.2f},{int(row['Volume'])}"
        )

    return "\n".join(csv_lines)
```

**Performance Metrics**:
```python
def _calculate_performance_metrics(historical_data: pd.DataFrame):
    """Calculate returns and volatility from historical data."""
    current_price = historical_data['Close'].iloc[-1]

    # Calculate returns
    performance_30d = (current_price / historical_data['Close'].iloc[-30] - 1) * 100
    performance_90d = (current_price / historical_data['Close'].iloc[-90] - 1) * 100
    performance_180d = (current_price / historical_data['Close'].iloc[-180] - 1) * 100
    performance_365d = (current_price / historical_data['Close'].iloc[0] - 1) * 100

    # Calculate 30-day annualized volatility
    returns_30d = historical_data['Close'].iloc[-30:].pct_change()
    volatility_30d = returns_30d.std() * (252 ** 0.5) * 100  # Annualize

    return {
        'performance_30d': round(performance_30d, 2),
        'performance_90d': round(performance_90d, 2),
        'performance_180d': round(performance_180d, 2),
        'performance_365d': round(performance_365d, 2),
        'volatility_30d': round(volatility_30d, 2)
    }
```

**JSON Validation**:
```python
# After Claude response
forecast_json = _extract_json_from_response(result['content'])

# Validate structure
if not _validate_forecast_structure(forecast_json):
    raise InvalidResponseError("Forecast missing required fields")

# Store parsed forecast
analysis = AnalysisResult(
    analysis_type='forecast',
    symbol='BTC',
    raw_response=result['content'],
    parsed_data=forecast_json,  # Full JSON structure
    expires_at=datetime.utcnow() + timedelta(hours=24)
)
```

---

## Cost Tracking

### Token Usage

**Typical Token Counts**:
- Global analysis: 1,500-2,000 tokens
- Position analysis: 800-1,200 tokens
- Forecast: 2,000-3,000 tokens (due to historical data)

**Claude Sonnet 4.5 Pricing** (as of Oct 2025):
- Input: $0.003 per 1K tokens
- Output: $0.015 per 1K tokens

**Approximate Costs**:
- Global analysis: $0.015-0.020 per request
- Position analysis: $0.010-0.015 per request
- Forecast: $0.020-0.030 per request

### Cost Optimization

**Cache Hit Rate**: ~75% (expected)
**Daily Usage** (estimate for active user):
- 10 global analyses
- 20 position analyses
- 5 forecasts

**Daily Cost Without Caching**: $0.60
**Daily Cost With Caching**: $0.15

**Monthly Cost**: ~$4.50 (with 75% cache hit rate)

---

## Testing

### Test Coverage

**Total Tests**: 181 (all passing ✅)

**Breakdown**:
- Prompt Management (F8.1): 103 tests
- Claude Integration (F8.2): 25 tests
- Global Analysis (F8.3): 15 tests
- Position Analysis (F8.4): 23 tests
- Forecasting (F8.5): 15 tests

### Test Categories

1. **Unit Tests**: Service methods, data collection, formatting
2. **Integration Tests**: Database operations, API endpoints
3. **Mock Tests**: Claude API calls (avoid real API usage in tests)
4. **Validation Tests**: JSON parsing, recommendation extraction

### Example Test

```python
@pytest.mark.asyncio
async def test_generate_global_analysis(db_session, mock_claude):
    """Test global analysis generation."""

    # Seed prompt
    await seed_default_prompts_async(db_session)

    # Mock data collector
    data_collector = MockDataCollector()
    data_collector.set_global_data({
        'portfolio_value': '25847.33',
        'position_count': '14',
        # ... other fields
    })

    # Mock Claude response
    mock_claude.set_response({
        'content': '## Market Analysis\n\n...',
        'tokens_used': 1523,
        'generation_time_ms': 2847
    })

    # Create service
    service = AnalysisService(
        db=db_session,
        claude_service=mock_claude,
        prompt_service=PromptService(db_session),
        data_collector=data_collector,
        cache_service=MockCache()
    )

    # Generate analysis
    result = await service.generate_global_analysis()

    # Assertions
    assert 'analysis' in result
    assert result['tokens_used'] == 1523
    assert result['cached'] == False

    # Check database storage
    stored = await db_session.execute(
        select(AnalysisResult).filter_by(analysis_type='global')
    )
    assert stored.scalar_one_or_none() is not None
```

---

## Troubleshooting

### Common Issues

#### 1. Missing API Key

**Error**: `ClaudeAPIError: API key not found`

**Solution**: Set `ANTHROPIC_API_KEY` in `.env` file
```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
```

#### 2. Rate Limit Exceeded

**Error**: `RateLimitError: Rate limit exceeded (50 req/min)`

**Solution**: Wait 60 seconds or increase `ANTHROPIC_RATE_LIMIT` in config

#### 3. Invalid Forecast JSON

**Error**: `InvalidResponseError: Could not extract JSON from response`

**Solution**: Claude sometimes wraps JSON in markdown. Extraction logic handles this, but if it fails, check `raw_response` in database for formatting issues.

#### 4. Missing Prompt Template

**Error**: `ValueError: Global analysis prompt not found`

**Solution**: Run seed script: `uv run python seed_prompts.py`

#### 5. Yahoo Finance API Timeout

**Error**: Historical price fetch fails for forecasts

**Solution**: Graceful degradation returns empty string. Check yfinance status or use cached data.

---

## Future Enhancements

### Planned Features

1. **Forecast Accuracy Tracking** (Future)
   - Compare predicted prices with actual prices
   - Calculate MAPE (Mean Absolute Percentage Error)
   - Display accuracy metrics in UI

2. **Custom Prompts** (Epic 9 Integration)
   - User-editable prompts via Settings UI
   - Prompt A/B testing
   - Version history and rollback

3. **Multi-Model Support**
   - Support for Claude Opus (more detailed analysis)
   - Support for Claude Haiku (faster, cheaper)
   - Model selection per analysis type

4. **Batch Analysis**
   - Analyze all positions in parallel
   - Generate daily reports
   - Email/notification integration

5. **Historical Analysis Archive**
   - Longer retention of analyses
   - Compare analysis over time
   - Track sentiment changes

---

## API Documentation

### Endpoints

Full API documentation available at: `http://localhost:8000/docs` (FastAPI OpenAPI)

**Quick Reference**:

| Endpoint | Method | Purpose | Cache TTL |
|----------|--------|---------|-----------|
| `/api/analysis/global` | GET | Portfolio-wide analysis | 1 hour |
| `/api/analysis/position/{symbol}` | GET | Single position analysis | 1 hour |
| `/api/analysis/forecast/{symbol}` | GET | Two-quarter forecast | 24 hours |
| `/api/analysis/positions/bulk` | POST | Bulk position analysis | 1 hour |
| `/api/analysis/forecasts/bulk` | POST | Bulk forecasts | 24 hours |

**Query Parameters**:
- `force_refresh` (bool) - Bypass cache and generate fresh analysis

**Response Format**:
- Global: `GlobalAnalysisResponse` (Markdown text)
- Position: `PositionAnalysisResponse` (Markdown + recommendation enum)
- Forecast: `ForecastResponse` (Structured JSON with scenarios)

---

## Files Reference

### Backend Files

**Core Services**:
- `backend/claude_service.py` - Claude API client (117 lines)
- `backend/analysis_service.py` - Analysis orchestration (245 lines)
- `backend/prompt_service.py` - Prompt CRUD operations (287 lines)
- `backend/prompt_renderer.py` - Template rendering + data collection (658 lines)

**API Layer**:
- `backend/analysis_router.py` - REST API endpoints (198 lines)
- `backend/analysis_schemas.py` - Pydantic request/response models (183 lines)
- `backend/prompt_router.py` - Prompt management API (266 lines)
- `backend/prompt_schemas.py` - Prompt schemas (148 lines)

**Configuration**:
- `backend/config.py` - Settings with Anthropic config (89 lines)
- `backend/seed_prompts.py` - Default prompt seeder (267 lines)

**Database**:
- `backend/models.py` - SQLAlchemy models (Prompt, PromptVersion, AnalysisResult)
- `backend/migrations/.../db531fc3eabe_epic_8_prompt_management_system.py` - Migration

### Frontend Files

**Components**:
- `frontend/src/pages/Analysis.tsx` - Main analysis page (215 lines)
- `frontend/src/components/GlobalAnalysisCard.tsx` - Global analysis display (142 lines)
- `frontend/src/components/PositionAnalysisList.tsx` - Position list (178 lines)
- `frontend/src/components/PositionAnalysisCard.tsx` - Position card (193 lines)
- `frontend/src/components/ForecastPanel.tsx` - Forecast charts (267 lines)

### Test Files

**Backend Tests**:
- `backend/tests/test_prompt_service.py` - 46 tests
- `backend/tests/test_prompt_renderer.py` - 39 tests
- `backend/tests/test_claude_service.py` - 14 tests
- `backend/tests/test_analysis_service.py` - 11 tests
- `backend/tests/test_analysis_router.py` - 8 tests
- `backend/tests/test_position_data_collection.py` - 12 tests
- `backend/tests/test_forecast_generation.py` - 15 tests

**Frontend Tests**:
- `frontend/src/components/GlobalAnalysisCard.test.tsx` - 8 tests
- `frontend/src/components/PositionAnalysisList.test.tsx` - 10 tests
- `frontend/src/components/ForecastPanel.test.tsx` - 12 tests

---

**Last Updated**: October 29, 2025
**Epic Status**: ✅ Complete (100%)
**Documentation Version**: 1.0
