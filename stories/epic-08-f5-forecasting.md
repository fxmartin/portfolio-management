## Feature 8.5: Forecasting Engine with Scenarios
**Feature Description**: Generate two-quarter forecasts with pessimistic, realistic, and optimistic scenarios
**User Value**: Make informed decisions based on data-driven predictions
**Priority**: High (Core differentiator)
**Complexity**: 15 story points

### Story F8.5-001: Forecast API
**Status**: 🔴 Not Started
**User Story**: As FX, I want two-quarter forecasts for my positions so that I can plan my investment strategy

**Acceptance Criteria**:
- **Given** I have a position
- **When** I request a forecast
- **Then** I receive Q1 and Q2 predictions
- **And** each quarter has pessimistic, realistic, and optimistic scenarios
- **And** each scenario includes target price and confidence %
- **And** each scenario includes key assumptions
- **And** each scenario includes risk factors
- **And** forecast is generated in <15 seconds
- **And** cached forecasts are returned if recent (< 24 hours)

**API Endpoint**:
```python
@router.get("/api/analysis/forecast/{symbol}", response_model=ForecastResponse)
async def get_forecast(
    symbol: str = Path(..., description="Asset symbol"),
    force_refresh: bool = Query(False),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Get two-quarter forecast with scenarios

    Returns pessimistic, realistic, and optimistic scenarios
    for Q1 and Q2 with confidence levels.
    """
    result = await analysis_service.generate_forecast(symbol, force_refresh)
    return ForecastResponse(**result)
```

**Response Models**:
```python
class ScenarioForecast(BaseModel):
    price: Decimal = Field(..., description="Target price for this scenario")
    confidence: int = Field(..., ge=0, le=100, description="Confidence percentage")
    assumptions: str = Field(..., description="Key assumptions driving this scenario")
    risks: str = Field(..., description="Main risk factors")

class QuarterForecast(BaseModel):
    pessimistic: ScenarioForecast
    realistic: ScenarioForecast
    optimistic: ScenarioForecast

class ForecastResponse(BaseModel):
    symbol: str
    current_price: Decimal
    q1_forecast: QuarterForecast
    q2_forecast: QuarterForecast
    overall_outlook: str = Field(..., description="2-3 sentence summary")
    generated_at: datetime
    tokens_used: int
    cached: bool

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTC-USD",
                "current_price": 45000.00,
                "q1_forecast": {
                    "pessimistic": {
                        "price": 38000.00,
                        "confidence": 70,
                        "assumptions": "Regulatory headwinds and risk-off sentiment",
                        "risks": "SEC enforcement actions, macro recession"
                    },
                    "realistic": {
                        "price": 52000.00,
                        "confidence": 65,
                        "assumptions": "Continued institutional adoption, ETF inflows",
                        "risks": "Market volatility, liquidity concerns"
                    },
                    "optimistic": {
                        "price": 68000.00,
                        "confidence": 45,
                        "assumptions": "Major institutional announcements, spot ETF approval",
                        "risks": "Overheating, regulatory surprise"
                    }
                },
                "q2_forecast": "{ ... similar structure ... }",
                "overall_outlook": "Bitcoin faces near-term volatility but strong fundamentals support medium-term upside. Institutional adoption remains key driver.",
                "generated_at": "2025-01-15T10:40:00Z",
                "tokens_used": 2156,
                "cached": False
            }
        }
```

**Bulk Forecast Endpoint**:
```python
@router.post("/api/analysis/forecasts/bulk", response_model=BulkForecastResponse)
async def get_bulk_forecasts(
    symbols: List[str] = Body(..., max_items=5),  # Limit to 5 for token management
    force_refresh: bool = Query(False),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Get forecasts for multiple positions (max 5)

    Use for portfolio-wide forecast generation.
    """
    results = await asyncio.gather(*[
        analysis_service.generate_forecast(symbol, force_refresh)
        for symbol in symbols
    ])

    return BulkForecastResponse(
        forecasts={
            symbol: ForecastResponse(**result)
            for symbol, result in zip(symbols, results)
        },
        total_tokens_used=sum(r['tokens_used'] for r in results)
    )

class BulkForecastResponse(BaseModel):
    forecasts: Dict[str, ForecastResponse]
    total_tokens_used: int
```

**Definition of Done**:
- [x] Single forecast endpoint
- [x] Bulk forecast endpoint (max 5)
- [x] Response models with validation
- [x] JSON parsing from Claude response
- [x] Forecast structure validation
- [x] Cache integration (24-hour TTL)
- [x] Error handling
- [x] Unit tests (≥85% coverage)
- [x] Integration tests
- [x] API documentation
- [x] Performance: <15s per forecast

**Story Points**: 8
**Priority**: Must Have
**Dependencies**: F8.2-002 (Analysis Service)
**Risk Level**: Medium (JSON parsing complexity)
**Assigned To**: Unassigned

---

### Story F8.5-002: Forecast Data Collection
**Status**: 🔴 Not Started
**User Story**: As the system, I want comprehensive historical and market data so that forecasts are well-grounded

**Acceptance Criteria**:
- **Given** a forecast request
- **When** collecting data
- **Then** current price and position data are included
- **And** 52-week price range is provided
- **And** 30-day and 90-day performance is calculated
- **And** market context (sector performance, indices) is included
- **And** relevant news sentiment is considered (optional enhancement)
- **And** data collection completes in <3 seconds

**Forecast Data Collection**:
```python
# Extend PromptDataCollector

async def collect_forecast_data(self, symbol: str) -> Dict[str, Any]:
    """Collect comprehensive data for forecast generation"""
    # Get position data
    position_data = await self.collect_position_data(symbol)

    # Get historical prices
    historical = await self._get_historical_prices(symbol, days=365)

    # Calculate performance metrics
    performance = self._calculate_performance_metrics(historical)

    # Get market context
    market_context = await self._build_market_context(position_data['asset_type'])

    return {
        **position_data,
        "week_52_low": float(min(historical) if historical else 0),
        "week_52_high": float(max(historical) if historical else 0),
        "performance_30d": performance['30d'],
        "performance_90d": performance['90d'],
        "performance_180d": performance['180d'],
        "performance_365d": performance['365d'],
        "volatility_30d": performance['volatility'],
        "market_context": market_context
    }

async def _get_historical_prices(self, symbol: str, days: int) -> List[float]:
    """Fetch historical prices from Yahoo Finance"""
    try:
        ticker = yf.Ticker(symbol)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        hist = ticker.history(start=start_date, end=end_date)
        return hist['Close'].tolist()
    except:
        return []

def _calculate_performance_metrics(self, prices: List[float]) -> Dict[str, float]:
    """Calculate various performance metrics from price history"""
    if not prices or len(prices) < 30:
        return {
            '30d': 0.0, '90d': 0.0, '180d': 0.0, '365d': 0.0,
            'volatility': 0.0
        }

    current = prices[-1]

    # Performance calculations
    perf_30d = ((current - prices[-30]) / prices[-30] * 100) if len(prices) >= 30 else 0
    perf_90d = ((current - prices[-90]) / prices[-90] * 100) if len(prices) >= 90 else 0
    perf_180d = ((current - prices[-180]) / prices[-180] * 100) if len(prices) >= 180 else 0
    perf_365d = ((current - prices[0]) / prices[0] * 100) if len(prices) >= 365 else 0

    # Volatility (30-day standard deviation of returns)
    if len(prices) >= 30:
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(-30, 0)]
        volatility = (sum((r - sum(returns)/len(returns))**2 for r in returns) / len(returns)) ** 0.5 * 100
    else:
        volatility = 0.0

    return {
        '30d': round(perf_30d, 2),
        '90d': round(perf_90d, 2),
        '180d': round(perf_180d, 2),
        '365d': round(perf_365d, 2),
        'volatility': round(volatility, 2)
    }

async def _build_market_context(self, asset_type: str) -> str:
    """Build narrative market context based on asset type"""
    context_parts = []

    # Get relevant indices
    if asset_type == 'stocks':
        sp500 = await self.yahoo_service.get_price('^GSPC')
        context_parts.append(f"S&P 500: {sp500.day_change_percent:+.2f}% today")
    elif asset_type == 'crypto':
        btc = await self.yahoo_service.get_price('BTC-USD')
        context_parts.append(f"Bitcoin (market leader): {btc.day_change_percent:+.2f}% today")
    elif asset_type == 'metals':
        gold = await self.yahoo_service.get_price('GC=F')
        context_parts.append(f"Gold: {gold.day_change_percent:+.2f}% today")

    # Add macro context (could be enhanced with news API)
    context_parts.append("Current market sentiment: Mixed with volatility concerns")

    return ". ".join(context_parts)
```

**Definition of Done**:
- [x] Forecast data collection implemented
- [x] Historical price fetching (365 days)
- [x] Performance metrics calculation (30d, 90d, 180d, 365d)
- [x] Volatility calculation
- [x] Market context building
- [x] Error handling for missing data
- [x] Unit tests (≥85% coverage)
- [x] Performance: <3s data collection

**Story Points**: 5
**Priority**: Must Have
**Dependencies**: F3.1-001 (Yahoo Finance)
**Risk Level**: Low
**Assigned To**: Unassigned

---

### Story F8.5-003: Forecast Accuracy Tracking
**Status**: 🔴 Not Started
**User Story**: As FX, I want to track forecast accuracy over time so that I can trust the predictions

**Acceptance Criteria**:
- **Given** forecasts have been generated
- **When** actual prices are known (end of quarter)
- **Then** forecast accuracy is calculated
- **And** comparison shows which scenario was closest
- **And** accuracy percentage is stored for each forecast
- **And** I can view historical forecast performance
- **And** accuracy metrics are displayed per symbol
- **And** overall forecasting accuracy is tracked

**Forecast Tracking Schema**:
```sql
CREATE TABLE forecast_tracking (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    forecast_date DATE NOT NULL,
    quarter VARCHAR(10) NOT NULL,  -- 'Q1', 'Q2'

    -- Original forecast
    pessimistic_price DECIMAL(20, 8) NOT NULL,
    pessimistic_confidence INTEGER NOT NULL,
    realistic_price DECIMAL(20, 8) NOT NULL,
    realistic_confidence INTEGER NOT NULL,
    optimistic_price DECIMAL(20, 8) NOT NULL,
    optimistic_confidence INTEGER NOT NULL,

    -- Actual outcome
    actual_price DECIMAL(20, 8),
    actual_date DATE,

    -- Accuracy metrics
    closest_scenario VARCHAR(20),  -- 'pessimistic', 'realistic', 'optimistic'
    accuracy_percentage DECIMAL(5, 2),  -- How close was the best scenario
    realistic_error_percentage DECIMAL(6, 2),  -- Error of realistic scenario

    created_at TIMESTAMP DEFAULT NOW(),
    evaluated_at TIMESTAMP
);

CREATE INDEX idx_forecast_symbol ON forecast_tracking(symbol);
CREATE INDEX idx_forecast_date ON forecast_tracking(forecast_date);
```

**Tracking Service**:
```python
class ForecastTrackingService:
    def __init__(self, db: Session):
        self.db = db

    async def record_forecast(
        self,
        symbol: str,
        forecast_data: ForecastResponse
    ):
        """Store forecast for later accuracy evaluation"""
        # Calculate target dates (end of Q1/Q2)
        today = date.today()
        q1_end = self._get_quarter_end(today, 1)
        q2_end = self._get_quarter_end(today, 2)

        # Store Q1 forecast
        q1_tracking = ForecastTracking(
            symbol=symbol,
            forecast_date=today,
            quarter='Q1',
            pessimistic_price=forecast_data.q1_forecast.pessimistic.price,
            pessimistic_confidence=forecast_data.q1_forecast.pessimistic.confidence,
            realistic_price=forecast_data.q1_forecast.realistic.price,
            realistic_confidence=forecast_data.q1_forecast.realistic.confidence,
            optimistic_price=forecast_data.q1_forecast.optimistic.price,
            optimistic_confidence=forecast_data.q1_forecast.optimistic.confidence
        )
        self.db.add(q1_tracking)

        # Store Q2 forecast
        q2_tracking = ForecastTracking(
            symbol=symbol,
            forecast_date=today,
            quarter='Q2',
            pessimistic_price=forecast_data.q2_forecast.pessimistic.price,
            pessimistic_confidence=forecast_data.q2_forecast.pessimistic.confidence,
            realistic_price=forecast_data.q2_forecast.realistic.price,
            realistic_confidence=forecast_data.q2_forecast.realistic.confidence,
            optimistic_price=forecast_data.q2_forecast.optimistic.price,
            optimistic_confidence=forecast_data.q2_forecast.optimistic.confidence
        )
        self.db.add(q2_tracking)

        self.db.commit()

    async def evaluate_forecasts(self):
        """
        Evaluate accuracy of forecasts that have reached their target date

        Run this daily to check for forecasts ready to evaluate
        """
        today = date.today()

        # Get forecasts ready for evaluation
        pending = self.db.query(ForecastTracking).filter(
            ForecastTracking.actual_price.is_(None),
            ForecastTracking.forecast_date <= today
        ).all()

        for forecast in pending:
            # Check if quarter has ended
            target_date = self._get_quarter_end(forecast.forecast_date, int(forecast.quarter[1]))
            if today >= target_date:
                await self._evaluate_single_forecast(forecast, target_date)

    async def _evaluate_single_forecast(
        self,
        forecast: ForecastTracking,
        target_date: date
    ):
        """Evaluate a single forecast against actual price"""
        # Fetch actual price on target date
        actual_price = await self._get_price_on_date(forecast.symbol, target_date)
        if not actual_price:
            return  # Wait for data

        # Calculate errors for each scenario
        errors = {
            'pessimistic': abs(float(actual_price) - float(forecast.pessimistic_price)) / float(actual_price) * 100,
            'realistic': abs(float(actual_price) - float(forecast.realistic_price)) / float(actual_price) * 100,
            'optimistic': abs(float(actual_price) - float(forecast.optimistic_price)) / float(actual_price) * 100
        }

        # Find closest scenario
        closest = min(errors.items(), key=lambda x: x[1])

        # Update tracking record
        forecast.actual_price = actual_price
        forecast.actual_date = target_date
        forecast.closest_scenario = closest[0]
        forecast.accuracy_percentage = 100 - closest[1]  # Accuracy = 100 - error
        forecast.realistic_error_percentage = errors['realistic']
        forecast.evaluated_at = datetime.utcnow()

        self.db.commit()

    async def get_accuracy_stats(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get forecast accuracy statistics"""
        query = self.db.query(ForecastTracking).filter(
            ForecastTracking.actual_price.isnot(None)
        )

        if symbol:
            query = query.filter(ForecastTracking.symbol == symbol)

        forecasts = query.all()

        if not forecasts:
            return {
                'total_forecasts': 0,
                'average_accuracy': 0,
                'realistic_accuracy': 0,
                'scenario_distribution': {}
            }

        # Calculate statistics
        scenario_counts = {'pessimistic': 0, 'realistic': 0, 'optimistic': 0}
        total_accuracy = 0
        total_realistic_error = 0

        for f in forecasts:
            scenario_counts[f.closest_scenario] += 1
            total_accuracy += f.accuracy_percentage
            total_realistic_error += abs(f.realistic_error_percentage)

        return {
            'total_forecasts': len(forecasts),
            'average_accuracy': round(total_accuracy / len(forecasts), 2),
            'realistic_accuracy': round(100 - (total_realistic_error / len(forecasts)), 2),
            'scenario_distribution': {
                k: round(v / len(forecasts) * 100, 1)
                for k, v in scenario_counts.items()
            }
        }

    def _get_quarter_end(self, start_date: date, quarter_offset: int) -> date:
        """Calculate end date of quarter N from start date"""
        # Simple implementation: 3 months per quarter
        end_month = start_date.month + (quarter_offset * 3)
        end_year = start_date.year + (end_month - 1) // 12
        end_month = ((end_month - 1) % 12) + 1

        # Last day of that month
        import calendar
        last_day = calendar.monthrange(end_year, end_month)[1]
        return date(end_year, end_month, last_day)

    async def _get_price_on_date(self, symbol: str, target_date: date) -> Optional[Decimal]:
        """Fetch historical price on specific date"""
        try:
            ticker = yf.Ticker(symbol)
            # Fetch a week of data around target date to handle weekends
            start = target_date - timedelta(days=7)
            end = target_date + timedelta(days=7)

            hist = ticker.history(start=start, end=end)

            # Find closest date
            closest_date = min(hist.index, key=lambda d: abs((d.date() - target_date).days))
            return Decimal(str(hist.loc[closest_date]['Close']))
        except:
            return None
```

**API Endpoints**:
```python
@router.get("/api/analysis/forecast-accuracy", response_model=AccuracyStatsResponse)
async def get_forecast_accuracy(
    symbol: Optional[str] = Query(None),
    tracking_service: ForecastTrackingService = Depends(get_tracking_service)
):
    """
    Get forecast accuracy statistics

    Returns overall accuracy metrics and scenario distribution.
    """
    stats = await tracking_service.get_accuracy_stats(symbol)
    return AccuracyStatsResponse(**stats)

class AccuracyStatsResponse(BaseModel):
    total_forecasts: int
    average_accuracy: float = Field(..., description="Average accuracy percentage")
    realistic_accuracy: float = Field(..., description="Accuracy of realistic scenarios")
    scenario_distribution: Dict[str, float] = Field(
        ...,
        description="Percentage of times each scenario was closest"
    )
```

**Definition of Done**:
- [x] Database schema for forecast tracking
- [x] Forecast recording on generation
- [x] Automated evaluation job (daily)
- [x] Accuracy calculation logic
- [x] Statistics API endpoint
- [x] Historical price fetching
- [x] Unit tests (≥85% coverage)
- [x] Integration tests
- [x] Documentation

**Story Points**: 5
**Priority**: Should Have (Nice to have for MVP, critical for long-term)
**Dependencies**: F8.5-001 (Forecast API)
**Risk Level**: Low
**Assigned To**: Unassigned

