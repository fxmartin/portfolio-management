## Feature 8.8: Strategy-Driven Portfolio Allocation
**Feature Description**: Personalized portfolio recommendations based on user-defined investment strategy using Claude AI
**User Value**: Get allocation and rebalancing advice tailored to personal investment philosophy, risk tolerance, and financial goals
**Priority**: High
**Complexity**: 13 story points (3 stories)

---

### Story F8.8-001: Investment Strategy Storage & API
**Status**: 🔴 Not Started
**User Story**: As FX, I want to define and store my investment strategy so that Claude can provide personalized recommendations aligned with my goals

**Acceptance Criteria**:
- **Given** I want to define my investment philosophy
- **When** I create or update my investment strategy
- **Then** the strategy is stored in the database
- **And** I can retrieve my current strategy
- **And** I can update my strategy at any time
- **And** the strategy supports rich text (multi-paragraph)
- **And** I can define multiple strategy components:
  - Overall investment goals (e.g., "15-20% YoY growth")
  - Risk tolerance (e.g., "medium risk")
  - Asset preferences (e.g., "mix of crypto and max 5 stocks/ETFs")
  - Profit-taking rules (e.g., "take profit at +20% and reinvest")
  - Geographic focus (e.g., "EU or emerging markets")
  - Sector preferences (e.g., "growing sectors")
  - Time horizon (e.g., "5-10 years")
  - Rebalancing frequency (e.g., "quarterly")

**Database Schema**:
```sql
-- Add to existing schema
CREATE TABLE investment_strategy (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1,  -- For future multi-user support
    strategy_text TEXT NOT NULL,

    -- Parsed components (optional, for UI hints)
    target_annual_return DECIMAL(5,2),  -- e.g., 17.5 for 17.5%
    risk_tolerance VARCHAR(20),  -- 'low', 'medium', 'high', 'custom'
    time_horizon_years INTEGER,
    max_positions INTEGER,
    profit_taking_threshold DECIMAL(5,2),  -- e.g., 20.0 for +20%

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    version INTEGER DEFAULT 1,

    CONSTRAINT unique_user_strategy UNIQUE (user_id)
);

-- Trigger to update version on changes
CREATE OR REPLACE FUNCTION update_strategy_version()
RETURNS TRIGGER AS $$
BEGIN
    NEW.version = OLD.version + 1;
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER strategy_version_trigger
    BEFORE UPDATE ON investment_strategy
    FOR EACH ROW
    EXECUTE FUNCTION update_strategy_version();
```

**SQLAlchemy Model**:
```python
# models.py
class InvestmentStrategy(Base):
    __tablename__ = "investment_strategy"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, default=1, unique=True)
    strategy_text = Column(Text, nullable=False)

    # Parsed components (optional)
    target_annual_return = Column(Numeric(5, 2), nullable=True)
    risk_tolerance = Column(String(20), nullable=True)
    time_horizon_years = Column(Integer, nullable=True)
    max_positions = Column(Integer, nullable=True)
    profit_taking_threshold = Column(Numeric(5, 2), nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    version = Column(Integer, default=1, nullable=False)
```

**Pydantic Schemas**:
```python
# strategy_schemas.py
from enum import Enum
from pydantic import BaseModel, Field, validator

class RiskTolerance(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CUSTOM = "custom"

class InvestmentStrategyCreate(BaseModel):
    strategy_text: str = Field(
        ...,
        min_length=50,
        max_length=5000,
        description="Detailed investment strategy in natural language"
    )
    target_annual_return: Optional[Decimal] = Field(None, ge=0, le=100)
    risk_tolerance: Optional[RiskTolerance] = None
    time_horizon_years: Optional[int] = Field(None, ge=1, le=50)
    max_positions: Optional[int] = Field(None, ge=1, le=100)
    profit_taking_threshold: Optional[Decimal] = Field(None, ge=0, le=1000)

    @validator('strategy_text')
    def strategy_must_be_meaningful(cls, v):
        if len(v.split()) < 20:
            raise ValueError('Strategy must contain at least 20 words for meaningful analysis')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "strategy_text": "I want to take regular profit whenever a position reaches +20% and reinvest it in other positions. Ultimate target is to generate 15 to 20% YoY growth. I am looking at medium risk investments with a mix of crypto and max 5 different stocks or ETFs in growing sectors in EU or emerging markets.",
                "target_annual_return": 17.5,
                "risk_tolerance": "medium",
                "time_horizon_years": 10,
                "max_positions": 5,
                "profit_taking_threshold": 20.0
            }
        }

class InvestmentStrategyUpdate(BaseModel):
    strategy_text: Optional[str] = Field(None, min_length=50, max_length=5000)
    target_annual_return: Optional[Decimal] = None
    risk_tolerance: Optional[RiskTolerance] = None
    time_horizon_years: Optional[int] = None
    max_positions: Optional[int] = None
    profit_taking_threshold: Optional[Decimal] = None

class InvestmentStrategyResponse(BaseModel):
    id: int
    user_id: int
    strategy_text: str
    target_annual_return: Optional[Decimal]
    risk_tolerance: Optional[str]
    time_horizon_years: Optional[int]
    max_positions: Optional[int]
    profit_taking_threshold: Optional[Decimal]
    created_at: datetime
    updated_at: datetime
    version: int

    class Config:
        from_attributes = True
```

**API Endpoints**:
```python
# strategy_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/strategy", tags=["Investment Strategy"])

@router.get("/", response_model=InvestmentStrategyResponse)
async def get_strategy(
    db: AsyncSession = Depends(get_db)
):
    """
    Get current investment strategy

    Returns the user's defined investment strategy.
    If no strategy exists, returns 404.
    """
    result = await db.execute(
        select(InvestmentStrategy).where(InvestmentStrategy.user_id == 1)
    )
    strategy = result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(404, "No investment strategy defined")

    return strategy

@router.post("/", response_model=InvestmentStrategyResponse, status_code=201)
async def create_strategy(
    strategy: InvestmentStrategyCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create investment strategy

    Creates a new investment strategy. Only one strategy per user.
    If strategy already exists, use PUT to update.
    """
    # Check if strategy already exists
    existing = await db.execute(
        select(InvestmentStrategy).where(InvestmentStrategy.user_id == 1)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(409, "Strategy already exists. Use PUT to update.")

    # Create new strategy
    db_strategy = InvestmentStrategy(
        user_id=1,
        **strategy.model_dump()
    )
    db.add(db_strategy)
    await db.commit()
    await db.refresh(db_strategy)

    return db_strategy

@router.put("/", response_model=InvestmentStrategyResponse)
async def update_strategy(
    strategy_update: InvestmentStrategyUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update investment strategy

    Updates existing strategy. Version is automatically incremented.
    """
    result = await db.execute(
        select(InvestmentStrategy).where(InvestmentStrategy.user_id == 1)
    )
    strategy = result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(404, "No strategy found. Use POST to create.")

    # Update fields
    update_data = strategy_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(strategy, field, value)

    await db.commit()
    await db.refresh(strategy)

    return strategy

@router.delete("/", status_code=204)
async def delete_strategy(
    db: AsyncSession = Depends(get_db)
):
    """
    Delete investment strategy

    Removes the current strategy. Use with caution.
    """
    result = await db.execute(
        select(InvestmentStrategy).where(InvestmentStrategy.user_id == 1)
    )
    strategy = result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(404, "No strategy found")

    await db.delete(strategy)
    await db.commit()

    return None
```

**Definition of Done**:
- [ ] Database migration with investment_strategy table
- [ ] SQLAlchemy model created
- [ ] Pydantic schemas with validation
- [ ] 4 API endpoints (GET, POST, PUT, DELETE)
- [ ] Version auto-increment on update
- [ ] Strategy text validation (min 20 words)
- [ ] Unit tests for API endpoints (≥85% coverage)
- [ ] Integration tests with database
- [ ] API documentation with examples

**Test Coverage Requirements**:
1. **Unit Tests** (12 tests minimum):
   - `test_create_strategy()`
   - `test_create_strategy_duplicate_fails()`
   - `test_get_strategy()`
   - `test_get_strategy_not_found()`
   - `test_update_strategy()`
   - `test_update_strategy_increments_version()`
   - `test_update_strategy_not_found()`
   - `test_delete_strategy()`
   - `test_delete_strategy_not_found()`
   - `test_strategy_text_too_short_fails()`
   - `test_strategy_text_minimum_words()`
   - `test_optional_fields_nullable()`

2. **Integration Tests** (5 tests minimum):
   - `test_full_strategy_lifecycle()`
   - `test_version_tracking_across_updates()`
   - `test_updated_at_changes_on_update()`
   - `test_strategy_persists_across_sessions()`
   - `test_parsed_components_stored_correctly()`

**Story Points**: 5
**Priority**: Must Have
**Dependencies**: None
**Risk Level**: Low
**Estimated Effort**: 4-6 hours
**Assigned To**: Unassigned

---

### Story F8.8-002: Claude Strategy-Driven Recommendations
**Status**: 🔴 Not Started
**User Story**: As FX, I want Claude to analyze my portfolio against my investment strategy so that I receive personalized allocation recommendations

**Acceptance Criteria**:
- **Given** I have defined my investment strategy
- **When** I request strategy-driven recommendations
- **Then** Claude receives my full investment strategy
- **And** Claude receives my current portfolio composition
- **And** Claude receives market context and position performance
- **And** Claude analyzes alignment between current portfolio and strategy
- **And** Claude identifies positions that don't fit the strategy
- **And** Claude recommends specific actions to align with strategy
- **And** Claude considers my profit-taking rules (e.g., +20% threshold)
- **And** Claude respects my constraints (e.g., max 5 positions)
- **And** recommendations include rationale tied to strategy
- **And** analysis completes in <20 seconds
- **And** results are cached for 12 hours

**Enhanced Strategy Analysis Prompt**:
```markdown
# Strategy-Driven Portfolio Analysis

You are a portfolio advisor helping align the portfolio with a specific investment strategy.

## Investment Strategy

{strategy_text}

### Strategy Components
- **Target Annual Return**: {target_annual_return}%
- **Risk Tolerance**: {risk_tolerance}
- **Time Horizon**: {time_horizon_years} years
- **Max Positions**: {max_positions}
- **Profit-Taking Rule**: Take profit at +{profit_taking_threshold}%

## Current Portfolio

**Total Value**: {portfolio_total_value}
**Number of Positions**: {position_count}

### All Positions with Performance

{positions_detail_table}
| Symbol | Asset Type | Quantity | Entry Price | Current Price | Value   | P&L    | P&L % | Holding Period |
|--------|-----------|----------|-------------|---------------|---------|--------|-------|----------------|
| BTC    | Crypto    | 0.1234   | €65,000     | €81,234       | €10,024 | +€2,005| +25%  | 180 days       |
| MSTR   | Stocks    | 19.68    | €210.00     | €248.50       | €4,890  | +€757  | +18%  | 90 days        |
| SOL    | Crypto    | 16.37    | €140.00     | €162.34       | €2,657  | +€365  | +16%  | 120 days       |
| ...    | ...       | ...      | ...         | ...           | ...     | ...    | ...   | ...            |

### Asset Allocation

{asset_allocation}
- Stocks: 55% (€27,500) across 8 positions
- Crypto: 35% (€17,500) across 5 positions
- Metals: 10% (€5,000) across 2 positions

**Total Positions**: 15

### Sector Allocation (Stocks)

{sector_allocation}
- Technology: 75% (6 positions)
- Finance: 20% (2 positions)
- Consumer: 5% (1 position)

### Geographic Exposure

{geographic_exposure}
- US: 60%
- EU: 25%
- Emerging Markets: 15%

## Market Context

{market_indices}
- S&P 500: 5,234 (+0.5% today)
- Bitcoin: $82,145 (+2.3% today)
- Gold: $2,145/oz (+0.1% today)

## Analysis Tasks

### 1. Strategy Alignment Assessment

Analyze how well the current portfolio aligns with the investment strategy:

- **Position Count**: Is {position_count} positions aligned with "{max_positions} max positions" rule?
- **Asset Mix**: Does the current allocation match strategy preferences?
- **Geographic Focus**: Is the portfolio focused on the right regions?
- **Sector Focus**: Are we invested in "growing sectors"?
- **Risk Level**: Does the portfolio match "{risk_tolerance}" risk tolerance?

### 2. Profit-Taking Opportunities

Identify positions that meet the profit-taking threshold:

- Which positions have reached or exceeded +{profit_taking_threshold}% gains?
- Should these positions be reduced or fully closed per the strategy?
- How should the profits be reinvested to maintain strategy alignment?

### 3. Position-Level Recommendations

For each position, assess:

- **Fits Strategy?**: Does this position align with the investment philosophy?
- **Action**: HOLD / REDUCE / CLOSE / INCREASE / MAINTAIN
- **Rationale**: Explain decision in context of the strategy

### 4. New Position Suggestions

Based on the strategy, suggest:

- New positions that would better align with the strategy
- Specific sectors or assets to consider
- Entry points and sizing

### 5. Portfolio Rebalancing Plan

Create a concrete action plan to align portfolio with strategy:

1. **Immediate Actions** (profit-taking at +{profit_taking_threshold}%):
   - Which positions to reduce/close
   - Expected proceeds

2. **Redeployment Plan**:
   - How to reinvest profits
   - New positions or existing positions to strengthen
   - Sizing and entry strategies

3. **Long-term Adjustments**:
   - Positions that don't fit strategy (to be gradually reduced)
   - Missing exposure areas to add over time

## Response Format

Return analysis in this JSON structure:

```json
{
  "summary": "Overall strategy alignment assessment in 2-3 sentences",
  "alignment_score": 7.5,  // 0-10 scale
  "key_insights": [
    "Portfolio has 15 positions, exceeding the 5 max limit from strategy",
    "BTC at +25% has exceeded the +20% profit-taking threshold",
    "Missing exposure to emerging markets as specified in strategy"
  ],
  "profit_taking_opportunities": [
    {
      "symbol": "BTC",
      "current_pnl_percentage": 25.0,
      "threshold": 20.0,
      "recommendation": "REDUCE_50_PERCENT",
      "expected_proceeds": 5012.00,
      "rationale": "Position exceeded +20% profit-taking threshold per your strategy. Take profits and redeploy to underweight areas.",

      // Transaction data ready for manual input
      "transaction_data": {
        "transaction_type": "SELL",
        "symbol": "BTC",
        "quantity": 0.0617,  // 50% of 0.1234 position
        "price": 81234.56,
        "total_value": 5012.00,
        "currency": "EUR",
        "notes": "Strategy profit-taking: +25% exceeds +20% threshold"
      }
    }
  ],
  "position_assessments": [
    {
      "symbol": "BTC",
      "fits_strategy": true,
      "action": "REDUCE",
      "target_reduction": 50,
      "rationale": "Crypto is part of strategy, but position has hit profit-taking threshold. Reduce by 50% to lock gains."
    },
    {
      "symbol": "XYZ",
      "fits_strategy": false,
      "action": "CLOSE",
      "rationale": "Position in US consumer discretionary does not align with strategy focus on EU/emerging markets growing sectors."
    }
  ],
  "new_position_suggestions": [
    {
      "asset_type": "stocks",
      "region": "emerging_markets",
      "sector": "technology",
      "rationale": "Strategy calls for emerging market exposure in growing sectors. Consider adding positions in this area.",
      "example_symbols": ["BABA", "TSM", "ASML"]
    }
  ],
  "action_plan": {
    "immediate_actions": [
      {
        "action": "SELL",
        "symbol": "BTC",
        "percentage": 50,
        "expected_proceeds": 5012.00,
        "timing": "Execute within 1 week",

        // Transaction data ready for manual input
        "transaction_data": {
          "transaction_type": "SELL",
          "symbol": "BTC",
          "quantity": 0.0617,
          "price": 81234.56,
          "total_value": 5012.00,
          "currency": "EUR",
          "notes": "Strategy immediate action: Profit-taking per +20% rule"
        }
      }
    ],
    "redeployment": [
      {
        "action": "BUY",
        "target_region": "emerging_markets",
        "target_sector": "technology",
        "allocation": 2500.00,
        "rationale": "Add missing emerging market exposure per strategy",
        "suggested_symbols": ["ASML", "TSM"],

        // Example transaction data for first suggested symbol
        "transaction_data": {
          "transaction_type": "BUY",
          "symbol": "ASML",  // First suggestion
          "quantity": 5,  // Example: ~€500/share × 5 = €2500
          "price": 500.00,  // Current market price (to be updated)
          "total_value": 2500.00,
          "currency": "EUR",
          "notes": "Strategy redeployment: Add EM tech exposure (ASML suggested)"
        }
      }
    ],
    "gradual_adjustments": [
      {
        "action": "REDUCE_POSITIONS",
        "reason": "Portfolio has 15 positions, target is max 5 per strategy",
        "approach": "Consolidate over 3-6 months into highest-conviction positions"
      }
    ]
  },
  "target_annual_return_assessment": {
    "current_ytd_return": 18.5,
    "target_return": 17.5,
    "on_track": true,
    "commentary": "Portfolio is tracking above target return. Profit-taking now will lock in gains while staying aligned with strategy."
  },
  "risk_assessment": "Medium - Portfolio aligns with medium risk tolerance. Diversified across crypto and stocks.",
  "next_review_date": "2025-04-01"
}
```
```

**Response Model**:
```python
class TransactionData(BaseModel):
    """Ready-to-execute transaction data for manual input"""
    transaction_type: str  # "BUY" or "SELL"
    symbol: str
    quantity: Decimal
    price: Decimal
    total_value: Decimal
    currency: str = "EUR"
    notes: str

class ProfitTakingOpportunity(BaseModel):
    symbol: str
    current_pnl_percentage: Decimal
    threshold: Decimal
    recommendation: str  # "REDUCE_25_PERCENT", "REDUCE_50_PERCENT", "CLOSE"
    expected_proceeds: Decimal
    rationale: str
    transaction_data: TransactionData  # NEW: Ready for transaction input

class PositionAssessment(BaseModel):
    symbol: str
    fits_strategy: bool
    action: str  # "HOLD", "REDUCE", "CLOSE", "INCREASE", "MAINTAIN"
    target_reduction: Optional[int] = None  # Percentage
    rationale: str

class NewPositionSuggestion(BaseModel):
    asset_type: str
    region: str
    sector: str
    rationale: str
    example_symbols: List[str]

class ActionPlanItem(BaseModel):
    action: str
    symbol: Optional[str] = None
    percentage: Optional[int] = None
    target_region: Optional[str] = None
    target_sector: Optional[str] = None
    allocation: Optional[Decimal] = None
    expected_proceeds: Optional[Decimal] = None
    timing: Optional[str] = None
    rationale: str
    reason: Optional[str] = None
    approach: Optional[str] = None
    suggested_symbols: Optional[List[str]] = None  # NEW: For BUY actions
    transaction_data: Optional[TransactionData] = None  # NEW: Ready for transaction input

class TargetReturnAssessment(BaseModel):
    current_ytd_return: Decimal
    target_return: Decimal
    on_track: bool
    commentary: str

class StrategyDrivenRecommendationResponse(BaseModel):
    summary: str
    alignment_score: Decimal = Field(..., ge=0, le=10)
    key_insights: List[str]
    profit_taking_opportunities: List[ProfitTakingOpportunity]
    position_assessments: List[PositionAssessment]
    new_position_suggestions: List[NewPositionSuggestion]
    action_plan: Dict[str, List[ActionPlanItem]]
    target_annual_return_assessment: TargetReturnAssessment
    risk_assessment: str
    next_review_date: str
    generated_at: datetime
    tokens_used: int
    cached: bool
```

**API Endpoint**:
```python
@router.get("/api/strategy/recommendations", response_model=StrategyDrivenRecommendationResponse)
async def get_strategy_recommendations(
    force_refresh: bool = Query(False),
    analysis_service: AnalysisService = Depends(get_analysis_service),
    strategy_service: StrategyService = Depends(get_strategy_service),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    """
    Get AI-powered recommendations aligned with investment strategy

    Analyzes portfolio against user's defined investment strategy.
    Returns specific actions to improve alignment.
    Results cached for 12 hours.
    """
    # Get strategy
    strategy = await strategy_service.get_strategy()
    if not strategy:
        raise HTTPException(404, "No investment strategy defined. Please create one first.")

    # Get portfolio data
    positions = await portfolio_service.get_all_positions()

    # Generate recommendations
    result = await analysis_service.generate_strategy_recommendations(
        strategy, positions, force_refresh
    )

    return result
```

**Definition of Done**:
- [ ] Strategy-driven analysis prompt created
- [ ] Prompt saved to database
- [ ] AnalysisService method for strategy recommendations
- [ ] JSON response parsing with complex nested structures
- [ ] Response models with Pydantic validation
- [ ] API endpoint with 12-hour caching
- [ ] Unit tests for prompt rendering (≥85% coverage)
- [ ] Integration tests with mocked Claude
- [ ] Manual test with real Claude API
- [ ] Performance: <20s generation time
- [ ] Error handling for missing strategy

**Test Coverage Requirements**:
1. **Unit Tests** (15 tests minimum):
   - `test_render_strategy_prompt()`
   - `test_parse_strategy_response_json()`
   - `test_identify_profit_taking_opportunities()`
   - `test_assess_position_alignment()`
   - `test_position_count_validation()`
   - `test_missing_strategy_raises_error()`
   - `test_cache_hit_returns_cached()`
   - `test_force_refresh_bypasses_cache()`
   - `test_profit_taking_threshold_calculation()`
   - `test_target_return_assessment()`
   - `test_risk_tolerance_matching()`
   - `test_geographic_exposure_analysis()`
   - `test_sector_alignment_check()`
   - `test_max_positions_constraint()`
   - `test_json_parsing_handles_complex_structure()`

2. **Integration Tests** (7 tests minimum):
   - `test_end_to_end_strategy_recommendations()`
   - `test_recommendations_with_profit_taking_positions()`
   - `test_recommendations_exceeding_max_positions()`
   - `test_recommendations_with_all_strategy_components()`
   - `test_recommendations_with_minimal_strategy()`
   - `test_strategy_update_clears_cache()`
   - `test_response_structure_validation()`

**Story Points**: 5
**Priority**: Must Have
**Dependencies**:
- F8.8-001 (Investment Strategy Storage)
- F8.2-002 (Analysis Service) ✅
- F8.4-002 (Position Context) ✅
**Risk Level**: Medium
**Estimated Effort**: 5-7 hours
**Assigned To**: Unassigned

---

### Story F8.8-003: Strategy Management UI
**Status**: 🔴 Not Started
**User Story**: As FX, I want a UI to define and edit my investment strategy so that I can easily update my goals and preferences

**Acceptance Criteria**:
- **Given** I want to define my investment strategy
- **When** I navigate to the Strategy page
- **Then** I see a form to input/edit my strategy
- **And** I can enter my strategy as free-form text
- **And** I can optionally specify structured fields (target return, risk, max positions, etc.)
- **And** I see my current strategy if one exists
- **And** I can see when the strategy was last updated and version number
- **And** I can save changes to update the strategy
- **And** I see a preview of how Claude will interpret my strategy
- **And** I can view my strategy-driven recommendations on the same page
- **And** the page updates recommendations when I save a new strategy

**UI Components**:

1. **StrategyPage** (`/strategy`):
   - Main container for strategy management
   - Strategy editor section
   - Recommendations section

2. **StrategyEditorCard**:
   - Large textarea for strategy text (5000 chars max)
   - Character counter
   - Word counter (minimum 20 words)
   - Optional structured fields:
     - Target Annual Return (% slider)
     - Risk Tolerance (dropdown: Low/Medium/High/Custom)
     - Time Horizon (years slider)
     - Max Positions (number input)
     - Profit-Taking Threshold (% slider)
   - Save button with loading state
   - Last updated timestamp and version
   - Example strategy templates (button to insert)

3. **StrategyTemplatesModal**:
   - Pre-written strategy examples:
     - **Conservative Growth**: "Focus on stable dividend stocks and bonds..."
     - **Balanced Growth**: "Mix of growth stocks and crypto with medium risk..."
     - **Aggressive Growth**: "High-growth tech stocks and crypto with high volatility..."
     - **Income Focus**: "Dividend-paying stocks and bond ETFs..."
     - **Value Investing**: "Undervalued stocks in established companies..."
   - "Use Template" button inserts text into editor

4. **StrategyRecommendationsCard**:
   - Alignment score gauge (0-10)
   - Key insights list
   - Profit-taking opportunities section with **transaction details**:
     - Symbol, P&L%, Threshold, Action
     - **Transaction**: Quantity × Price = Total
     - Rationale
     - **Action buttons**: 📋 Copy | ➕ Create Transaction | ✓ Planned
   - Position assessments table:
     - Symbol, Action, Fits Strategy?, Rationale
     - Color-coded actions (green=HOLD, yellow=REDUCE, red=CLOSE)
   - New position suggestions with **suggested symbols**
   - Action plan accordion (Immediate/Redeployment/Gradual) with **transaction data**
   - **Export All Actions** button (CSV download)
   - Next review date

5. **AlignmentScoreGauge**:
   - Circular progress indicator
   - Color gradient: Red (0-4), Yellow (5-7), Green (8-10)
   - Large number display
   - Label: "Strategy Alignment"

**Visual Design**:
```
┌─────────────────────────────────────────────────────────────┐
│  Investment Strategy                   [📊 View Recommendations] │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─── Define Your Strategy ─────────────────────────────┐   │
│  │                                                        │   │
│  │  ┌────────────────────────────────────────────────┐  │   │
│  │  │ I want to take regular profit whenever a      │  │   │
│  │  │ position reaches +20% and reinvest it in      │  │   │
│  │  │ other positions. Ultimate target is to        │  │   │
│  │  │ generate 15 to 20% YoY growth. I am looking   │  │   │
│  │  │ at medium risk investments with a mix of      │  │   │
│  │  │ crypto and max 5 different stocks or ETFs     │  │   │
│  │  │ in growing sectors in EU or emerging markets. │  │   │
│  │  └────────────────────────────────────────────────┘  │   │
│  │  245 / 5000 characters | 42 words ✓                   │   │
│  │                                                        │   │
│  │  Optional Details:                                     │   │
│  │  Target Return: [=====>----] 17.5%                   │   │
│  │  Risk Tolerance: [Medium ▼]                          │   │
│  │  Max Positions: [5]                                   │   │
│  │  Profit-Taking: [=====>----] 20%                     │   │
│  │                                                        │   │
│  │  [Use Template]  [Save Strategy]                      │   │
│  │  Last updated: Oct 29, 2025 | Version 3              │   │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─── Strategy-Driven Recommendations ───────────────────┐  │
│  │                                                         │  │
│  │  Alignment Score: ● 7.5/10                            │  │
│  │                                                         │  │
│  │  🔑 Key Insights:                                      │  │
│  │  • Portfolio has 15 positions, exceeding 5 max limit  │  │
│  │  • BTC at +25% has exceeded +20% profit threshold     │  │
│  │  • Missing emerging markets exposure                  │  │
│  │                                                         │  │
│  │  💰 Profit-Taking Opportunities (1):                  │  │
│  │  ┌─────────────────────────────────────────────────┐ │  │
│  │  │ BTC  +25% (Your Threshold: +20%)               │ │  │
│  │  │ Action: SELL 0.0617 @ €81,234 = €5,012        │ │  │
│  │  │ Rationale: "Lock in gains per strategy rule"   │ │  │
│  │  │ [📋 Copy] [➕ Create Transaction] [✓ Planned]  │ │  │
│  │  └─────────────────────────────────────────────────┘ │  │
│  │                                                         │  │
│  │  📋 Position Assessments (15):                        │  │
│  │  | Symbol | Action   | Fits? | Rationale           | │  │
│  │  |--------|----------|-------|---------------------| │  │
│  │  | BTC    | REDUCE   | ✓     | Hit profit threshold| │  │
│  │  | MSTR   | HOLD     | ✓     | Aligned with...     | │  │
│  │  | XYZ    | CLOSE    | ✗     | Wrong geography     | │  │
│  │                                                         │  │
│  │  ➕ New Position Suggestions (2):                     │  │
│  │  • Emerging Markets Tech ETF (BABA, TSM)             │  │
│  │  • EU Growth Sector ETF (ASML)                       │  │
│  │                                                         │  │
│  │  📅 Next Review: April 1, 2025                        │  │
│  └─────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
```

**API Integration**:
```typescript
// StrategyPage.tsx
const saveStrategy = async (strategyData: StrategyFormData) => {
  setLoading(true);

  try {
    // Create or update strategy
    const method = existingStrategy ? 'PUT' : 'POST';
    const response = await fetch('/api/strategy', {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(strategyData)
    });

    const savedStrategy = await response.json();
    setStrategy(savedStrategy);

    // Fetch recommendations with new strategy
    const recsResponse = await fetch('/api/strategy/recommendations?force_refresh=true');
    const recommendations = await recsResponse.json();
    setRecommendations(recommendations);

    toast.success('Strategy saved and recommendations updated!');
  } catch (error) {
    toast.error('Failed to save strategy');
  } finally {
    setLoading(false);
  }
};
```

**State Management**:
```typescript
interface StrategyState {
  strategy: InvestmentStrategy | null;
  recommendations: StrategyDrivenRecommendationResponse | null;
  loading: boolean;
  saving: boolean;
  showTemplates: boolean;
  formData: {
    strategy_text: string;
    target_annual_return?: number;
    risk_tolerance?: 'low' | 'medium' | 'high' | 'custom';
    time_horizon_years?: number;
    max_positions?: number;
    profit_taking_threshold?: number;
  };
  validationErrors: string[];
}
```

**Definition of Done**:
- [ ] StrategyPage component created
- [ ] StrategyEditorCard with textarea and structured fields
- [ ] StrategyTemplatesModal with 5 example strategies
- [ ] StrategyRecommendationsCard component
- [ ] AlignmentScoreGauge component with color gradient
- [ ] Character and word counters
- [ ] Form validation (min 20 words, max 5000 chars)
- [ ] Save functionality (POST/PUT detection)
- [ ] Auto-refresh recommendations after save
- [ ] **NEW: Copy transaction data to clipboard (per action)**
- [ ] **NEW: Create Transaction button (pre-populates Epic 7 form)**
- [ ] **NEW: Export All Actions button (CSV download)**
- [ ] Mark actions as planned/completed
- [ ] Loading states during save and recommendation fetch
- [ ] Toast notifications for success/error
- [ ] Navigation: "Strategy" tab in sidebar (🎯 Target icon)
- [ ] Responsive design (mobile-friendly)
- [ ] Unit tests for all components (≥85% coverage)
- [ ] Integration tests with mocked API
- [ ] Test clipboard copy functionality
- [ ] Test navigation to transaction form with prefill

**Test Coverage Requirements**:
1. **Component Tests** (25 tests minimum):
   - `test_strategy_page_renders()`
   - `test_load_existing_strategy()`
   - `test_create_new_strategy()`
   - `test_update_existing_strategy()`
   - `test_strategy_text_validation_min_words()`
   - `test_strategy_text_validation_max_chars()`
   - `test_character_counter_updates()`
   - `test_word_counter_updates()`
   - `test_save_button_disabled_when_invalid()`
   - `test_templates_modal_opens()`
   - `test_template_insertion()`
   - `test_recommendations_load_after_save()`
   - `test_alignment_score_gauge_colors()`
   - `test_profit_taking_opportunities_display()`
   - `test_position_assessments_table()`
   - `test_action_color_coding()`
   - `test_new_position_suggestions_display()`
   - `test_action_plan_accordion()`
   - `test_loading_state_during_save()`
   - `test_error_handling_save_failure()`
   - `test_success_toast_on_save()`
   - `test_structured_fields_optional()`
   - `test_sliders_update_values()`
   - `test_version_increment_display()`
   - `test_last_updated_timestamp()`

**Story Points**: 3
**Priority**: Must Have
**Dependencies**:
- F8.8-001 (Investment Strategy Storage)
- F8.8-002 (Claude Strategy-Driven Recommendations)
**Risk Level**: Low
**Estimated Effort**: 3-5 hours
**Assigned To**: Unassigned

**Technical Notes**:
- Use React Hook Form for form management
- Debounce autosave (optional enhancement)
- Consider markdown support for strategy text (future enhancement)
- Store strategy templates in constants file for easy updates

---

## Feature Summary

**Total Story Points**: 13 (5 + 5 + 3)
**Total Stories**: 3
**Estimated Development Time**: 12-18 hours
**Priority**: High

**Value Proposition**:
Transform generic allocation advice into **personalized strategy-driven recommendations**. Instead of "rebalance to 60/25/15", get "Your BTC hit +25%, exceeding your +20% profit-taking rule. Sell 50% (€5,012) and redeploy to emerging markets tech ETFs to better align with your EU/emerging markets focus while staying under your 5-position limit."

**Success Metrics**:
- Strategy definition rate: >80% of users
- Recommendation engagement: Strategy page visited weekly
- Action implementation: >60% of profit-taking recommendations executed
- Strategy updates: Quarterly reviews leading to strategy refinements
