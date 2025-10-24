# Epic 2: Portfolio Calculation Engine

## Epic Overview
**Epic ID**: EPIC-02
**Epic Name**: Portfolio Calculation Engine
**Epic Description**: Calculate accurate portfolio positions, cost basis, and P&L using FIFO methodology
**Business Value**: Provide accurate financial calculations matching manual verification within 5%
**User Impact**: See true portfolio performance including realized and unrealized gains
**Success Metrics**: FIFO calculations match manual Excel calculations, handle multi-currency transactions
**Status**: ✅ Complete

## Features in this Epic
- Feature 2.1: FIFO Cost Basis Calculator ✅
- Feature 2.2: Position Aggregation ✅
- Feature 2.3: P&L Calculations ✅
- Feature 2.4: Currency Conversion ✅

## Progress Tracking
| Feature | Stories | Points | Status | Progress |
|---------|---------|--------|--------|----------|
| F2.1: FIFO Calculator | 1 | 8 | ✅ Complete | 100% (8/8 pts) |
| F2.2: Position Aggregation | 1 | 5 | ✅ Complete | 100% (5/5 pts) |
| F2.3: P&L Calculations | 2 | 8 | ✅ Complete | 100% (8/8 pts) |
| F2.4: Currency Conversion | 1 | 5 | ✅ Complete | 100% (5/5 pts) |
| **Total** | **5** | **26** | **✅ Complete** | **100% (26/26 pts)** |

---

## Feature 2.1: FIFO Cost Basis Calculator
**Feature Description**: Implement First-In-First-Out methodology for accurate cost basis tracking
**User Value**: Accurate tax reporting and true investment performance metrics
**Priority**: High
**Complexity**: 8 story points

### Story F2.1-001: Implement FIFO Algorithm
**Status**: ✅ Complete (Enhanced Oct 24, 2025)
**User Story**: As FX, I want my cost basis calculated using FIFO methodology so that my P&L is accurate for tax purposes
**Implementation**: `backend/fifo_calculator.py` - 27 tests, 94% coverage

**Recent Enhancement (Issue #4)**:
- Transaction fees now included in cost basis calculation
- Added optional `fee` parameter to `add_purchase()` method
- Adjusted price calculation: `(price × quantity + fee) / quantity`
- Improves accuracy from 99% to 99.77% match with Koinly
- Added 5 comprehensive fee handling test scenarios
- Commit: `57ea793`

**Acceptance Criteria**:
- **Given** multiple BUY transactions for the same ticker at different prices
- **When** a SELL transaction occurs
- **Then** the oldest shares are sold first (FIFO)
- **And** cost basis is calculated from oldest purchases
- **And** remaining shares retain their purchase prices
- **And** partial sells are handled correctly
- **And** the calculation can be audited with lot details

**Technical Requirements**:
- Lot tracking system for each purchase
- Queue-based FIFO implementation
- Support for partial lot sales
- Audit trail for tax reporting
- Handle stock splits and dividends

**Algorithm Design**:
```python
class FIFOCalculator:
    def __init__(self):
        self.lots = {}  # ticker -> deque of Lot objects

    def add_purchase(self, ticker, quantity, price, date):
        # Add new lot to the queue

    def process_sale(self, ticker, quantity, sale_price, date):
        # Remove lots from queue in FIFO order
        # Calculate realized P&L
        # Return cost basis and remaining lots
```

**Definition of Done**:
- [x] FIFO algorithm implemented with lot tracking
- [x] Handles partial sells correctly
- [x] Maintains complete lot history
- [x] Transaction fees included in cost basis
- [x] Unit tests with multiple scenarios (27 tests)
- [x] Performance tested with 1000+ transactions
- [x] Audit report generation capability
- [x] Documentation with examples
- [x] Validates against Koinly (99.77% accuracy)

**Story Points**: 8
**Priority**: Must Have
**Dependencies**: F1.3-001 (Store Transactions)
**Risk Level**: High
**Assigned To**: Unassigned

**Test Scenarios**:
```python
# Scenario 1: Basic FIFO
BUY 100 @ $10 on Jan 1
BUY 100 @ $15 on Feb 1
SELL 150 @ $20 on Mar 1
# Expected: Realize profit on 100@$10 + 50@$15

# Scenario 2: Multiple partial sells
BUY 100 @ $10
SELL 30 @ $12
SELL 30 @ $14
SELL 40 @ $16
# Expected: All from first lot, different realized P&L

# Scenario 3: Complete position closure
BUY 50 @ $20
BUY 50 @ $25
SELL 100 @ $30
# Expected: Position closed, all P&L realized
```

---

## Feature 2.2: Position Aggregation
**Feature Description**: Calculate current holdings by aggregating all transactions
**User Value**: Clear view of what assets are currently owned and their quantities
**Priority**: High
**Complexity**: 5 story points

### Story F2.2-001: Calculate Current Holdings
**Status**: ✅ Complete (Enhanced Oct 24, 2025)
**User Story**: As FX, I want to see my current positions aggregated by ticker so that I know what I own
**Implementation**: `backend/portfolio_service.py` - 11 tests, 92% coverage

**Recent Enhancement (Issue #3)**:
- Auto-recalculate positions after CSV imports
- Ensures all transactions (BUY, SELL, STAKING, AIRDROP, MINING) are included
- Fixed bug where recent staking rewards were not included in calculations
- Import endpoint now calls `PortfolioService.recalculate_all_positions()`
- Commit: `57ea793`

**Acceptance Criteria**:
- **Given** all transactions for a ticker
- **When** calculating current position
- **Then** total quantity owned is sum of buys minus sells
- **And** average cost basis is weighted average of remaining lots
- **And** positions with zero quantity are marked as closed
- **And** cash position is tracked from TOPUP/CARD_PAYMENT transactions
- **And** dividends are included in position history

**Technical Requirements**:
- Position aggregation service
- Weighted average calculation
- Cash balance tracking
- Position status (open/closed)
- Historical position snapshots

**Data Model**:
```python
class Position:
    ticker: str
    quantity: Decimal
    avg_cost_basis: Decimal
    total_cost: Decimal
    realized_pl: Decimal
    unrealized_pl: Decimal
    first_purchase_date: datetime
    last_transaction_date: datetime
    status: str  # 'open' or 'closed'

class CashPosition:
    currency: str
    balance: Decimal
    last_updated: datetime
```

**Definition of Done**:
- [x] Position aggregation logic implemented
- [x] Weighted average cost calculation
- [x] Handle fully closed positions
- [x] Cash balance tracking from all sources
- [x] Position history tracking
- [x] Auto-recalculate after imports
- [x] Support all transaction types (BUY, SELL, STAKING, AIRDROP, MINING)
- [x] Unit tests for edge cases
- [x] Integration with FIFO calculator

**Story Points**: 5
**Priority**: Must Have
**Dependencies**: F2.1-001 (FIFO Algorithm)
**Risk Level**: Medium
**Assigned To**: Unassigned

---

## Feature 2.3: P&L Calculations
**Feature Description**: Calculate both realized and unrealized profit/loss
**User Value**: Understand true investment performance and tax implications
**Priority**: High
**Complexity**: 8 story points total

### Story F2.3-001: Calculate Unrealized P&L
**Status**: ✅ Complete
**User Story**: As FX, I want to see my unrealized gains/losses so that I know my paper profits
**Implementation**: `backend/portfolio_service.py` (update_position_price) - 4 tests

**Acceptance Criteria**:
- **Given** current positions with cost basis
- **When** calculating unrealized P&L
- **Then** P&L = (Current Price - Average Cost) × Quantity
- **And** P&L percentage = (Current Price / Average Cost - 1) × 100
- **And** values update when prices change
- **And** currency conversion is applied if needed
- **And** both position-level and portfolio-level P&L are calculated

**Technical Requirements**:
- Real-time P&L calculation
- Percentage calculation
- Multi-currency support
- Aggregation at portfolio level

**Calculation Formula**:
```python
unrealized_pl = (current_price - avg_cost) * quantity
unrealized_pl_pct = ((current_price / avg_cost) - 1) * 100
total_unrealized = sum(position.unrealized_pl for position in positions)
```

**Definition of Done**:
- [x] Unrealized P&L calculation implemented
- [x] Percentage calculation included
- [x] Real-time updates with price changes
- [x] Handle multiple currencies
- [x] Portfolio-level aggregation
- [x] Unit tests for calculations
- [x] Integration with live prices

**Story Points**: 3
**Priority**: Must Have
**Dependencies**: F2.2-001 (Current Holdings), F3.1-001 (Live Prices)
**Risk Level**: Low
**Assigned To**: Unassigned

---

### Story F2.3-002: Calculate Realized P&L
**Status**: ✅ Complete
**User Story**: As FX, I want to track my realized gains/losses so that I know my actual profits
**Implementation**: `backend/portfolio_service.py` (get_realized_pnl) - 3 tests

**Acceptance Criteria**:
- **Given** completed sell transactions with FIFO cost basis
- **When** calculating realized P&L
- **Then** profit/loss from each sale is recorded
- **And** FIFO cost basis is used for calculation
- **And** fees are included in calculation
- **And** running total is maintained by year
- **And** breakdown by ticker is available

**Technical Requirements**:
- Integration with FIFO calculator
- Fee handling in P&L
- Historical tracking by period
- Tax year aggregation

**Realized P&L Tracking**:
```python
class RealizedPL:
    transaction_id: int
    ticker: str
    sale_date: datetime
    quantity: Decimal
    sale_price: Decimal
    cost_basis: Decimal
    fees: Decimal
    realized_pl: Decimal
    tax_year: int

    @property
    def net_pl(self):
        return self.realized_pl - self.fees
```

**Definition of Done**:
- [x] Realized P&L tracking implemented
- [x] Integration with FIFO calculator
- [x] Fee handling in calculations
- [x] Historical P&L tracking
- [x] Tax year aggregation
- [x] Export capability for tax reporting
- [x] Unit tests for various scenarios

**Story Points**: 5
**Priority**: Should Have
**Dependencies**: F2.1-001 (FIFO Algorithm)
**Risk Level**: Medium
**Assigned To**: Unassigned

---

## Feature 2.4: Currency Conversion
**Feature Description**: Convert multi-currency portfolio to single base currency
**User Value**: See total portfolio value in preferred currency
**Priority**: High
**Complexity**: 5 story points

### Story F2.4-001: Single Base Currency Conversion
**Status**: ✅ Complete
**User Story**: As FX, I want all values converted to a single base currency so that I can see my total portfolio value
**Implementation**: `backend/currency_converter.py` - 19 tests, 94% coverage

**Acceptance Criteria**:
- **Given** transactions in multiple currencies (USD, EUR, GBP)
- **When** calculating portfolio value
- **Then** all values are converted to base currency
- **And** current exchange rates are used for unrealized values
- **And** historical rates are used for realized P&L (optional)
- **And** base currency is configurable (EUR or USD)
- **And** original currency amounts are preserved

**Technical Requirements**:
- Exchange rate service
- Configurable base currency
- Currency conversion utilities
- Cache exchange rates
- Preserve original values

**Currency Conversion Design**:
```python
class CurrencyConverter:
    def __init__(self, base_currency='USD'):
        self.base_currency = base_currency
        self.rates = {}  # Cache exchange rates

    def convert(self, amount, from_currency, to_currency=None):
        # Convert amount from one currency to another
        # Use base_currency if to_currency not specified

    def get_rate(self, from_currency, to_currency):
        # Fetch from Yahoo Finance or cache

    def convert_portfolio(self, positions):
        # Convert all positions to base currency
```

**Definition of Done**:
- [x] Currency conversion logic implemented
- [x] Configurable base currency setting
- [x] Exchange rate fetching (Yahoo Finance)
- [x] Rate caching for performance
- [x] Original values preserved in database
- [x] Handle missing exchange rates gracefully
- [x] Unit tests for conversion logic

**Story Points**: 5
**Priority**: Must Have
**Dependencies**: F2.2-001 (Position Aggregation)
**Risk Level**: Medium
**Assigned To**: Unassigned

---

## Technical Design Notes

### Calculation Pipeline
```python
1. Load Transactions: Fetch from database ordered by date
2. Build Lots: Create FIFO queue for each ticker
3. Process Sales: Apply FIFO to calculate cost basis
4. Aggregate Positions: Sum current holdings
5. Calculate P&L: Both realized and unrealized
6. Currency Conversion: Convert to base currency
7. Return Results: Formatted portfolio data
```

### Performance Optimization
- Cache position calculations (invalidate on new transaction)
- Batch calculate P&L for all positions
- Use decimal precision for financial calculations
- Index database by ticker and date

### Data Integrity
- All calculations use Decimal type (not float)
- Transaction atomicity for updates
- Audit trail for all calculations
- Validation of calculation results

---

## Dependencies
- **External**: Transaction data from Epic 1, Live prices from Epic 3
- **Internal**: FIFO must complete before P&L calculations
- **Libraries**: decimal, pandas, numpy for calculations

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|---------|------------|
| FIFO complexity | Wrong tax calculations | Extensive testing, audit trails |
| Floating point errors | Incorrect P&L | Use Decimal type throughout |
| Currency rate issues | Wrong portfolio value | Cache rates, fallback values |
| Performance with large portfolios | Slow calculations | Caching, batch processing |

## Testing Strategy

**⚠️ MANDATORY TESTING REQUIREMENT**:
- **Minimum Coverage Threshold**: 85% code coverage for all modules
- **No story is complete without passing tests meeting this threshold**

1. **Unit Tests** (Required - 85% minimum coverage): Each calculation function isolated
2. **Integration Tests** (Required): Full calculation pipeline
3. **Reconciliation Tests**: Compare with Excel calculations
4. **Edge Cases**: Zero positions, negative balances
5. **Performance Tests**: 10,000 transaction portfolio

## Definition of Done for Epic
- [x] All 5 stories completed
- [x] FIFO algorithm correctly tracks cost basis
- [x] Positions accurately aggregated
- [x] P&L calculations match manual verification
- [x] Multi-currency support working
- [x] Calculations complete in <1 second for 1000 transactions
- [x] Audit trail for all calculations
- [x] Unit test coverage ≥85% (mandatory threshold) - **93% achieved**
- [x] Documentation with calculation examples

## Implementation Summary

**Total Test Coverage**: 93% across 3 modules (403 statements)
**Total Tests**: 59 tests across 4 test files

### Files Created:
- `backend/fifo_calculator.py` - FIFO cost basis calculator (137 lines, 94% coverage)
- `backend/portfolio_service.py` - Position aggregation and P&L (154 lines, 92% coverage)
- `backend/currency_converter.py` - Currency conversion service (112 lines, 94% coverage)
- `backend/tests/test_fifo_calculator.py` - 22 tests
- `backend/tests/test_portfolio_service.py` - 11 tests
- `backend/tests/test_pnl_calculations.py` - 7 tests
- `backend/tests/test_currency_converter.py` - 19 tests

### Key Features:
- **FIFO Calculator**: Deque-based lot tracking with chronological ordering, audit trails
- **Portfolio Service**: Database-integrated position tracking, cost lot persistence
- **P&L Calculations**: Both realized and unrealized, with fee tracking
- **Currency Conversion**: Yahoo Finance integration, smart caching, 16 currencies supported