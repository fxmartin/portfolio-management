## Feature 8.7: AI-Powered Portfolio Rebalancing Recommendations
**Feature Description**: Intelligent portfolio rebalancing suggestions using Claude AI to optimize allocation and reduce concentration risk
**User Value**: Actionable recommendations on what to buy/sell to achieve target allocation with specific quantities and rationale
**Priority**: High
**Complexity**: 18 story points (3 stories)

---

### Story F8.7-001: Rebalancing Analysis Engine
**Status**: 🔴 Not Started
**User Story**: As FX, I want the system to analyze my portfolio allocation against target allocations so that I can identify rebalancing opportunities

**Acceptance Criteria**:
- **Given** I have a portfolio with multiple positions
- **When** I request a rebalancing analysis
- **Then** the system calculates current allocation percentages
- **And** compares current allocation to target allocation
- **And** identifies overweight positions (>5% above target)
- **And** identifies underweight positions (>5% below target)
- **And** calculates rebalancing delta for each asset type
- **And** generates preliminary rebalancing actions (buy/sell candidates)
- **And** calculation completes in <2 seconds

**Target Allocation Models**:

1. **Moderate Portfolio** (Default):
   - Stocks: 60%
   - Crypto: 25%
   - Metals: 15%

2. **Aggressive Portfolio**:
   - Stocks: 50%
   - Crypto: 40%
   - Metals: 10%

3. **Conservative Portfolio**:
   - Stocks: 70%
   - Crypto: 15%
   - Metals: 15%

4. **Custom** (user-defined percentages)

**Rebalancing Thresholds**:
- **Trigger threshold**: ±5% deviation from target (e.g., stocks at 55% when target is 60%)
- **Rebalancing band**: ±2% tolerance zone (don't rebalance if within 58-62% for 60% target)
- **Minimum trade**: €50 (don't suggest trades smaller than this)

**Rebalancing Analysis Data Structure**:
```python
class AssetTypeAllocation(BaseModel):
    asset_type: AssetType
    current_value: Decimal
    current_percentage: Decimal
    target_percentage: Decimal
    deviation: Decimal  # current - target
    status: AllocationStatus  # OVERWEIGHT, UNDERWEIGHT, BALANCED
    rebalancing_needed: bool
    delta_value: Decimal  # EUR amount to buy/sell
    delta_percentage: Decimal

class AllocationStatus(str, Enum):
    OVERWEIGHT = "OVERWEIGHT"  # > target + 5%
    UNDERWEIGHT = "UNDERWEIGHT"  # < target - 5%
    SLIGHTLY_OVERWEIGHT = "SLIGHTLY_OVERWEIGHT"  # target + 2% to target + 5%
    SLIGHTLY_UNDERWEIGHT = "SLIGHTLY_UNDERWEIGHT"  # target - 5% to target - 2%
    BALANCED = "BALANCED"  # within ±2%

class RebalancingAnalysis(BaseModel):
    total_portfolio_value: Decimal
    current_allocation: List[AssetTypeAllocation]
    target_model: str  # "moderate", "aggressive", "conservative", "custom"
    rebalancing_required: bool
    total_trades_needed: int
    estimated_transaction_costs: Decimal

    # Summary metrics
    largest_deviation: Decimal  # e.g., -15% (stocks underweight)
    most_overweight: Optional[str]  # e.g., "crypto"
    most_underweight: Optional[str]  # e.g., "stocks"

    generated_at: datetime
```

**API Endpoint**:
```python
@router.get("/api/rebalancing/analysis", response_model=RebalancingAnalysis)
async def get_rebalancing_analysis(
    target_model: str = Query("moderate", enum=["moderate", "aggressive", "conservative", "custom"]),
    custom_stocks: Optional[int] = Query(None, ge=0, le=100),
    custom_crypto: Optional[int] = Query(None, ge=0, le=100),
    custom_metals: Optional[int] = Query(None, ge=0, le=100),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    """
    Analyze portfolio allocation vs target and identify rebalancing needs

    Returns current allocation, deviations, and preliminary rebalancing data.
    """
    # Validate custom allocations sum to 100%
    if target_model == "custom":
        if not (custom_stocks and custom_crypto and custom_metals):
            raise HTTPException(400, "Custom model requires all allocation percentages")
        if custom_stocks + custom_crypto + custom_metals != 100:
            raise HTTPException(400, "Custom allocations must sum to 100%")

    analysis = await portfolio_service.analyze_rebalancing(
        target_model, custom_stocks, custom_crypto, custom_metals
    )
    return analysis
```

**Implementation Tasks**:
1. **RebalancingService** (`rebalancing_service.py`):
   - `analyze_allocation()` - Calculate current allocation percentages
   - `calculate_deviations()` - Compare current vs target
   - `identify_rebalancing_actions()` - Determine what needs rebalancing
   - `estimate_transaction_costs()` - Factor in trading fees

2. **Target Allocation Models** (`rebalancing_models.py`):
   - Predefined models (moderate/aggressive/conservative)
   - Custom model validation

3. **Rebalancing Schemas** (`rebalancing_schemas.py`):
   - Pydantic models for requests/responses
   - Enums for allocation status

**Definition of Done**:
- [ ] RebalancingService with allocation analysis
- [ ] Support for 3 predefined models + custom
- [ ] Deviation calculation with thresholds (±5% trigger, ±2% tolerance)
- [ ] API endpoint with query parameters
- [ ] Response includes all allocation data
- [ ] Unit tests for allocation logic (≥85% coverage)
- [ ] Integration tests with real portfolio data
- [ ] Performance: <2s analysis time
- [ ] Documentation with example responses

**Test Coverage Requirements**:
1. **Unit Tests** (12 tests minimum):
   - `test_calculate_current_allocation()`
   - `test_calculate_deviations_moderate_model()`
   - `test_calculate_deviations_aggressive_model()`
   - `test_calculate_deviations_conservative_model()`
   - `test_calculate_deviations_custom_model()`
   - `test_identify_overweight_positions()`
   - `test_identify_underweight_positions()`
   - `test_balanced_portfolio_no_rebalancing()`
   - `test_custom_allocation_validation()`
   - `test_custom_allocation_must_sum_to_100()`
   - `test_minimum_trade_threshold()`
   - `test_estimate_transaction_costs()`

2. **Integration Tests** (5 tests minimum):
   - `test_rebalancing_analysis_with_real_portfolio()`
   - `test_empty_portfolio_handling()`
   - `test_single_asset_type_portfolio()`
   - `test_extreme_concentration_detection()`
   - `test_api_endpoint_moderate_model()`

**Story Points**: 8
**Priority**: Must Have
**Dependencies**:
- F2.2-001 (Portfolio Service) ✅
- F8.4-003 (Portfolio Context Integration) - Recommended
**Risk Level**: Medium
**Estimated Effort**: 6-8 hours
**Assigned To**: Unassigned

**Technical Notes**:
- Use Decimal for all financial calculations (avoid float rounding errors)
- Cache allocation analysis for 5 minutes (portfolio changes infrequently)
- Consider transaction costs when suggesting rebalancing
- Don't suggest tiny trades (<€50) - not worth the fees
- Round suggested amounts to 2 decimal places for EUR

---

### Story F8.7-002: Claude-Powered Rebalancing Recommendations
**Status**: 🔴 Not Started
**User Story**: As FX, I want AI-powered rebalancing recommendations so that I receive specific buy/sell actions with quantities and rationale

**Acceptance Criteria**:
- **Given** I have a rebalancing analysis showing deviations
- **When** I request AI rebalancing recommendations
- **Then** Claude receives the full allocation analysis
- **And** Claude receives current positions with prices
- **And** Claude generates specific buy/sell recommendations
- **And** recommendations include exact symbols, quantities, and EUR amounts
- **And** recommendations include rationale for each action
- **And** recommendations consider market conditions and position context
- **And** recommendations are ordered by priority (largest deviations first)
- **And** total recommendation generation completes in <15 seconds
- **And** recommendations are cached for 6 hours

**Enhanced Rebalancing Prompt**:
```markdown
# Portfolio Rebalancing Analysis

You are a portfolio advisor helping with rebalancing recommendations.

## Current Portfolio State

**Total Value**: {portfolio_total_value}
**Target Allocation Model**: {target_model}

## Current Allocation vs Target

{allocation_table}
| Asset Type | Current % | Target % | Deviation | Status       | Delta (EUR) |
|------------|-----------|----------|-----------|--------------|-------------|
| Stocks     | 55%       | 60%      | -5%       | Underweight  | +€2,500     |
| Crypto     | 35%       | 25%      | +10%      | Overweight   | -€5,000     |
| Metals     | 10%       | 15%      | -5%       | Underweight  | +€2,500     |

## Current Positions

{positions_table}
| Symbol | Asset Type | Quantity | Current Price | Value   | % of Portfolio |
|--------|-----------|----------|---------------|---------|----------------|
| MSTR   | Stocks    | 19.68    | €248.50       | €4,890  | 9.8%           |
| BTC    | Crypto    | 0.1234   | €81,234.56    | €10,024 | 20.1%          |
| ...    | ...       | ...      | ...           | ...     | ...            |

## Market Context

{market_indices}
- S&P 500: 5,234 (+0.5% today)
- Bitcoin: $82,145 (+2.3% today)
- Gold: $2,145/oz (+0.1% today)

## Instructions

Generate specific rebalancing recommendations to achieve the target allocation:

1. **Identify specific positions to reduce** (OVERWEIGHT assets)
   - Which symbols to sell and how much
   - Consider current market conditions and tax implications
   - Prioritize positions with gains to minimize losses

2. **Identify specific positions to increase or new positions to open** (UNDERWEIGHT assets)
   - Which symbols to buy and how much
   - Consider diversification within the asset type
   - Suggest specific entry points if possible

3. **Prioritize recommendations** by largest deviations first

4. **Provide rationale** for each recommendation explaining:
   - Why this specific position
   - How it addresses the allocation gap
   - Market timing considerations
   - Risk/reward assessment

5. **Consider practical constraints**:
   - Minimum trade sizes (don't suggest trades <€50)
   - Transaction costs (assume 0.5% per trade)
   - Avoid creating too many small positions

## Response Format

Return recommendations in this JSON structure:

```json
{
  "summary": "Overall rebalancing strategy summary in 2-3 sentences",
  "priority": "HIGH|MEDIUM|LOW based on deviation severity",
  "recommendations": [
    {
      "action": "SELL",
      "symbol": "BTC",
      "asset_type": "crypto",
      "quantity": 0.05,
      "current_price": 81234.56,
      "estimated_value": 4061.73,
      "rationale": "Reduce crypto exposure from 35% to 25%. BTC is overweight and currently showing strength (+2.3% today) - good opportunity to lock in gains.",
      "priority": 1,
      "timing": "Consider selling into current strength (+2.3% today)",

      // Transaction data ready for manual input
      "transaction_data": {
        "transaction_type": "SELL",
        "symbol": "BTC",
        "quantity": 0.05,
        "price": 81234.56,
        "total_value": 4061.73,
        "currency": "EUR",
        "notes": "Rebalancing: Reduce crypto from 35% to 25% target"
      }
    },
    {
      "action": "BUY",
      "symbol": "MSTR",
      "asset_type": "stocks",
      "quantity": 10,
      "current_price": 248.50,
      "estimated_value": 2485.00,
      "rationale": "Increase stocks to 60% target. MSTR provides crypto exposure while counting as stocks, aligning with growth strategy.",
      "priority": 2,
      "timing": "Execute within 1 week",

      // Transaction data ready for manual input
      "transaction_data": {
        "transaction_type": "BUY",
        "symbol": "MSTR",
        "quantity": 10,
        "price": 248.50,
        "total_value": 2485.00,
        "currency": "EUR",
        "notes": "Rebalancing: Increase stocks to 60% target"
      }
    },
    ...
  ],
  "expected_outcome": {
    "stocks_percentage": 60,
    "crypto_percentage": 25,
    "metals_percentage": 15,
    "total_trades": 5,
    "estimated_costs": 125.50,
    "net_allocation_improvement": "+15% closer to target"
  },
  "risk_assessment": "Low - Recommendations diversified across asset types...",
  "implementation_notes": "Execute in 2-3 tranches over 1 week to minimize market impact"
}
```
```

**Response Model**:
```python
class RebalancingAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class TransactionData(BaseModel):
    """Ready-to-execute transaction data for manual input"""
    transaction_type: str  # "BUY" or "SELL"
    symbol: str
    quantity: Decimal
    price: Decimal
    total_value: Decimal
    currency: str = "EUR"
    notes: str

class RebalancingRecommendation(BaseModel):
    action: RebalancingAction
    symbol: str
    asset_type: AssetType
    quantity: Decimal
    current_price: Decimal
    estimated_value: Decimal
    rationale: str
    priority: int  # 1 = highest
    timing: Optional[str]
    transaction_data: TransactionData  # NEW: Ready for transaction input

class ExpectedOutcome(BaseModel):
    stocks_percentage: Decimal
    crypto_percentage: Decimal
    metals_percentage: Decimal
    total_trades: int
    estimated_costs: Decimal
    net_allocation_improvement: str

class RebalancingRecommendationResponse(BaseModel):
    summary: str
    priority: str  # "HIGH", "MEDIUM", "LOW"
    recommendations: List[RebalancingRecommendation]
    expected_outcome: ExpectedOutcome
    risk_assessment: str
    implementation_notes: str
    generated_at: datetime
    tokens_used: int
    cached: bool
```

**API Endpoint**:
```python
@router.get("/api/rebalancing/recommendations", response_model=RebalancingRecommendationResponse)
async def get_rebalancing_recommendations(
    target_model: str = Query("moderate"),
    force_refresh: bool = Query(False),
    analysis_service: AnalysisService = Depends(get_analysis_service),
    rebalancing_service: RebalancingService = Depends(get_rebalancing_service)
):
    """
    Get AI-powered rebalancing recommendations

    Uses Claude to generate specific buy/sell actions with rationale.
    Results cached for 6 hours.
    """
    # Get allocation analysis
    analysis = await rebalancing_service.analyze_rebalancing(target_model)

    # If balanced, return empty recommendations
    if not analysis.rebalancing_required:
        return RebalancingRecommendationResponse(
            summary="Your portfolio is well-balanced. No rebalancing needed.",
            priority="LOW",
            recommendations=[],
            expected_outcome=...,
            risk_assessment="None - portfolio is balanced",
            implementation_notes="Review allocation quarterly",
            generated_at=datetime.utcnow(),
            tokens_used=0,
            cached=False
        )

    # Generate AI recommendations
    result = await analysis_service.generate_rebalancing_recommendations(
        analysis, force_refresh
    )
    return result
```

**Definition of Done**:
- [ ] Rebalancing prompt template created
- [ ] Prompt saved to database with variables
- [ ] AnalysisService method for rebalancing recommendations
- [ ] JSON response parsing with validation
- [ ] Response models with Pydantic
- [ ] API endpoint with caching (6 hours)
- [ ] Unit tests for prompt rendering (≥85% coverage)
- [ ] Integration tests with mocked Claude
- [ ] Manual test with real Claude API
- [ ] Performance: <15s generation time
- [ ] Error handling for JSON parsing failures

**Test Coverage Requirements**:
1. **Unit Tests** (10 tests minimum):
   - `test_render_rebalancing_prompt()`
   - `test_parse_rebalancing_json_response()`
   - `test_validate_recommendation_quantities()`
   - `test_validate_recommendation_priorities()`
   - `test_balanced_portfolio_no_recommendations()`
   - `test_extreme_deviation_high_priority()`
   - `test_cache_hit_returns_cached_result()`
   - `test_force_refresh_bypasses_cache()`
   - `test_json_parsing_error_handling()`
   - `test_invalid_json_structure_handling()`

2. **Integration Tests** (5 tests minimum):
   - `test_end_to_end_rebalancing_recommendations()`
   - `test_moderate_model_recommendations()`
   - `test_aggressive_model_recommendations()`
   - `test_custom_model_recommendations()`
   - `test_recommendation_response_structure()`

**Story Points**: 5
**Priority**: Must Have
**Dependencies**:
- F8.7-001 (Rebalancing Analysis Engine)
- F8.2-002 (Analysis Service) ✅
**Risk Level**: Medium
**Estimated Effort**: 4-6 hours
**Assigned To**: Unassigned

---

### Story F8.7-003: Rebalancing UI Dashboard
**Status**: 🔴 Not Started
**User Story**: As FX, I want a visual rebalancing dashboard so that I can easily understand and act on rebalancing recommendations

**Acceptance Criteria**:
- **Given** I have rebalancing recommendations
- **When** I navigate to the Rebalancing page
- **Then** I see a visual allocation chart (current vs target)
- **And** I see a summary of required changes
- **And** I see a prioritized list of buy/sell recommendations
- **And** each recommendation shows symbol, action, quantity, value, and rationale
- **And** I can select a target allocation model (moderate/aggressive/conservative/custom)
- **And** I can expand each recommendation to see full details
- **And** I can toggle between compact and detailed views
- **And** the page updates in <2 seconds when changing models

**UI Components**:

1. **RebalancingPage** (`/rebalancing`):
   - Main container for rebalancing feature
   - Model selector dropdown
   - Allocation comparison section
   - Recommendations list
   - Implementation timeline

2. **AllocationComparisonChart**:
   - Side-by-side bar chart (current vs target)
   - Color coding: red (overweight), green (underweight), gray (balanced)
   - Shows deviation percentages
   - Interactive tooltips with EUR values

3. **RebalancingSummaryCard**:
   - Total trades needed
   - Estimated transaction costs
   - Expected improvement
   - Priority badge (HIGH/MEDIUM/LOW)
   - Quick stats (largest deviation, most overweight, most underweight)

4. **RebalancingRecommendationsList**:
   - Prioritized list of recommendations
   - Each item shows:
     - Action badge (BUY/SELL with color coding)
     - Symbol and asset type
     - **Transaction details**: Quantity × Price = Total Value
     - Rationale (expandable)
     - Timing suggestion
   - Expandable details with full analysis
   - **NEW: Action buttons**:
     - 📋 **Copy Transaction Data** - Copy to clipboard as CSV
     - ➕ **Create Transaction** - Pre-populate manual transaction form (links to Epic 7)
     - ✓ **Mark as Planned** - Track execution intent
     - ✓ **Mark as Completed** - Track execution status

5. **CustomAllocationModal**:
   - Input fields for custom percentages
   - Real-time validation (must sum to 100%)
   - Slider inputs with percentage display
   - Preview of what allocation would look like

**Transaction Data Export**:
```typescript
// Copy to clipboard functionality
const copyTransactionData = (recommendation: RebalancingRecommendation) => {
  const csv = `Type,Symbol,Quantity,Price,Total,Currency,Notes
${recommendation.transaction_data.transaction_type},${recommendation.transaction_data.symbol},${recommendation.transaction_data.quantity},${recommendation.transaction_data.price},${recommendation.transaction_data.total_value},${recommendation.transaction_data.currency},"${recommendation.transaction_data.notes}"`;

  navigator.clipboard.writeText(csv);
  toast.success('Transaction data copied to clipboard');
};

// Navigate to transaction form with pre-populated data
const createTransaction = (recommendation: RebalancingRecommendation) => {
  const txData = recommendation.transaction_data;
  navigate('/transactions', {
    state: {
      prefill: {
        transaction_type: txData.transaction_type,
        symbol: txData.symbol,
        quantity: txData.quantity,
        price: txData.price,
        currency: txData.currency,
        notes: txData.notes,
        source: 'REBALANCING_RECOMMENDATION'
      }
    }
  });
};
```

**Visual Design**:
```
┌─────────────────────────────────────────────────────────────┐
│  Rebalancing Dashboard           [Moderate ▼] [Export All] │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─── Allocation Comparison ───────────────────────────┐    │
│  │                                                       │    │
│  │  Current    Target                                   │    │
│  │  ┌───────┐  ┌───────┐                               │    │
│  │  │ 55% 📈│  │ 60% 📈│  Stocks  (UNDERWEIGHT -5%)    │    │
│  │  └───────┘  └───────┘                               │    │
│  │                                                       │    │
│  │  ┌───────┐  ┌───────┐                               │    │
│  │  │ 35% 💰│  │ 25% 💰│  Crypto  (OVERWEIGHT +10%)    │    │
│  │  └───────┘  └───────┘                               │    │
│  │                                                       │    │
│  │  ┌───────┐  ┌───────┐                               │    │
│  │  │ 10% 🥇│  │ 15% 🥇│  Metals  (UNDERWEIGHT -5%)    │    │
│  │  └───────┘  └───────┘                               │    │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─── Summary ──────────────────────────────────────────┐   │
│  │  Priority: HIGH     Trades: 5     Est. Cost: €125    │   │
│  │  Improvement: +15% closer to target allocation       │   │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─── Recommendations (5) ──────────────────────────────┐   │
│  │                                                        │   │
│  │  🔴 SELL  1  BTC                                      │   │
│  │     Quantity: 0.05  Price: €81,234  Total: €4,062   │   │
│  │     Rationale: Reduce crypto from 35% to 25%...      │   │
│  │     [📋 Copy] [➕ Create Transaction] [✓ Planned]    │   │
│  │                                                        │   │
│  │  🟢 BUY   2  MSTR                                     │   │
│  │     Quantity: 10  Price: €248.50  Total: €2,485      │   │
│  │     Rationale: Increase stocks exposure...           │   │
│  │     [📋 Copy] [➕ Create Transaction] [✓ Planned]    │   │
│  │                                                        │   │
│  │  🔴 SELL  3  ETH          1.5 @ €1,800   = €2,700    │   │
│  │     Rationale: Further reduce crypto...          ▼   │   │
│  │                                                        │   │
│  │  🟢 BUY   4  XAU          5.2 @ €480     = €2,496    │   │
│  │     Rationale: Increase metals to 15%...         ▼   │   │
│  │                                                        │   │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  📋 Implementation Notes:                                    │
│  Execute in 2-3 tranches over 1 week to minimize impact     │
└───────────────────────────────────────────────────────────────┘
```

**API Integration**:
```typescript
// RebalancingPage.tsx
const fetchRebalancingData = async (model: string) => {
  const [analysis, recommendations] = await Promise.all([
    fetch(`/api/rebalancing/analysis?target_model=${model}`),
    fetch(`/api/rebalancing/recommendations?target_model=${model}`)
  ]);

  setAnalysis(await analysis.json());
  setRecommendations(await recommendations.json());
};
```

**State Management**:
```typescript
interface RebalancingState {
  selectedModel: 'moderate' | 'aggressive' | 'conservative' | 'custom';
  customAllocation: { stocks: number; crypto: number; metals: number } | null;
  analysis: RebalancingAnalysis | null;
  recommendations: RebalancingRecommendationResponse | null;
  loading: boolean;
  expandedRecommendations: Set<number>;
  completedActions: Set<number>;
}
```

**Definition of Done**:
- [ ] RebalancingPage component created
- [ ] AllocationComparisonChart with Recharts
- [ ] RebalancingSummaryCard component
- [ ] RebalancingRecommendationsList component
- [ ] CustomAllocationModal component
- [ ] Model selector with 4 options
- [ ] Expand/collapse recommendation details
- [ ] **NEW: Copy transaction data to clipboard**
- [ ] **NEW: Create Transaction button (pre-populates Epic 7 form)**
- [ ] Mark recommendations as planned/completed
- [ ] **NEW: Export All Transactions button (CSV download)**
- [ ] Responsive design (mobile-friendly)
- [ ] Loading states and error handling
- [ ] Navigation: "Rebalancing" tab in sidebar (⚖️ Scale icon)
- [ ] Unit tests for all components (≥85% coverage)
- [ ] Integration tests with mocked API
- [ ] Visual regression tests for charts
- [ ] Test clipboard copy functionality
- [ ] Test navigation to transaction form with prefill

**Test Coverage Requirements**:
1. **Component Tests** (20 tests minimum):
   - `test_rebalancing_page_renders()`
   - `test_model_selector_changes_data()`
   - `test_custom_allocation_modal()`
   - `test_custom_allocation_validation()`
   - `test_allocation_comparison_chart_displays()`
   - `test_overweight_shown_in_red()`
   - `test_underweight_shown_in_green()`
   - `test_balanced_shown_in_gray()`
   - `test_summary_card_displays_metrics()`
   - `test_recommendations_list_renders()`
   - `test_recommendations_sorted_by_priority()`
   - `test_expand_recommendation_details()`
   - `test_collapse_recommendation_details()`
   - `test_mark_recommendation_completed()`
   - `test_buy_action_badge_green()`
   - `test_sell_action_badge_red()`
   - `test_loading_state_displays_spinner()`
   - `test_error_state_displays_message()`
   - `test_balanced_portfolio_no_recommendations()`
   - `test_responsive_layout_mobile()`

**Story Points**: 5
**Priority**: Must Have
**Dependencies**:
- F8.7-002 (Claude-Powered Rebalancing Recommendations)
- F8.6-001 (Analysis UI Components) ✅
**Risk Level**: Low
**Estimated Effort**: 4-6 hours
**Assigned To**: Unassigned

**Technical Notes**:
- Use Recharts for allocation comparison chart
- Implement optimistic UI updates (mark as completed instantly, sync with backend)
- Consider adding "export rebalancing plan" to PDF
- Color palette: Green (BUY), Red (SELL), Gray (balanced)

---

## Feature Summary

**Total Story Points**: 18 (8 + 5 + 5)
**Total Stories**: 3
**Estimated Development Time**: 14-20 hours
**Priority**: High

**Value Proposition**:
Transform raw allocation data into actionable intelligence. FX gets specific buy/sell recommendations with quantities, timing, and rationale - all powered by Claude AI's understanding of market context and portfolio strategy.

**Success Metrics**:
- Analysis generation: <2 seconds
- Recommendation generation: <15 seconds
- User engagement: Rebalancing page viewed weekly
- Implementation rate: >50% of recommendations acted upon
