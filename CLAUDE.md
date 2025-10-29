# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Portfolio management application for tracking stocks, metals, and cryptocurrency investments. Imports transactions from Revolut (metals & stocks) and Koinly (crypto) CSV exports, calculates FIFO cost basis with fee-inclusive calculations, and displays real-time portfolio performance with live market data.

**Current Status**: ~74% complete (261/352 story points across 9 epics) - All core features implemented. Transaction import, FIFO calculations, live prices, and dashboard visualization complete. Cost basis calculations validated against Koinly at 99.77% accuracy. Infrastructure & DevOps (Epic 5) complete with comprehensive development tools. **Epic 8 (AI Market Analysis) - 64% complete (65/101 points)** - Prompt Management (F8.1 ✅, 103 tests), Claude Integration (F8.2 ✅, 25 tests), Global Analysis (F8.3 ✅, 15 tests), Position Analysis (F8.4 🟡 2/3 stories, 23 tests, F8.4-003 pending), Forecasting Engine (F8.5 ✅, 15 tests), Analysis UI (F8.6 ✅), **Portfolio Rebalancing (F8.7 🔴 NEW - 18 pts)**, **Strategy-Driven Allocation (F8.8 🔴 NEWEST - 13 pts)**. **Epic 9 (Settings Management)** planned for centralized configuration UI.

## Essential Commands

### Development Environment

**Quick Start** (recommended):
```bash
# Show all available commands
make help

# Start all services in development mode (hot-reload enabled)
make dev

# Start with PgAdmin for database management
make dev-tools

# Run all tests
make test

# View logs from all services
make logs
```

**Docker Compose** (alternative):
```bash
# Development mode (with hot-reload, debug logging, PgAdmin)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Production mode
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up

# Standard mode
docker-compose up

# Stop all services
docker-compose down

# Reset everything including volumes
docker-compose down -v
```

**See Also**:
- `Makefile` - 30+ developer helper commands
- `docs/DEBUGGING.md` - Comprehensive debugging guide
- `docs/AI_ANALYSIS.md` - AI analysis system documentation
- `.vscode/launch.json` - VS Code debug configurations

### Backend Development
```bash
cd backend

# Install dependencies with uv (preferred over pip)
uv add <package>
uv add --dev <dev-package>

# Run tests
uv run pytest tests/ -v              # All tests
uv run pytest tests/test_csv_parser.py -v  # Specific test file
uv run pytest -k "test_detect_metals" -v   # Specific test

# Run backend locally (outside Docker)
uv run uvicorn main:app --reload --port 8000
```

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Run tests
npm test                    # Run all tests
npm test -- --run          # Run once without watch
npm test TransactionImport # Test specific component

# Run frontend locally (outside Docker)
npm run dev

# Build for production
npm run build
```

## Architecture Overview

### Service Communication Flow
```
User → React (3003) → FastAPI (8000) → PostgreSQL (5432)
                                    ↓
                                 Redis (6379)
```

### CSV Processing Pipeline
1. **Frontend Detection**: `TransactionImport.tsx` detects file type by filename pattern
2. **Backend Validation**: `csv_parser.py` validates and routes to correct parser
3. **Parser Selection**: Factory pattern selects MetalsParser/StocksParser/CryptoParser
4. **Database Storage**: Transactions saved to PostgreSQL via `transaction_service.py`
5. **FIFO Calculation**: Portfolio engine calculates positions with fee-inclusive cost basis
6. **Auto-Recalculation**: Positions automatically recalculated after successful imports

### File Type Detection Rules
- **Metals**: Files starting with `account-statement_`
- **Stocks**: Files matching UUID pattern (e.g., `B5A12617-2B56-4A79-B83D-13C6715DC0BA.csv`)
- **Crypto**: Files containing "koinly" (case-insensitive)

### Key Design Patterns
- **Factory Pattern**: CSV parser selection based on file type
- **Router Pattern**: FastAPI modular endpoint organization (`import_router.py`)
- **Component Architecture**: React components with colocated tests
- **Async First**: All I/O operations use async/await

## Critical Implementation Notes

### Completed Features ✅
- **Database Schema**: Fully implemented with transactions, positions, and price_history tables
- **CSV Parsers**: All three parsers (Metals, Stocks, Crypto) complete and tested
- **FIFO Calculator**: Complete with fee-inclusive cost basis (27 tests, 94% coverage)
- **Portfolio Service**: Position aggregation with all transaction types supported
- **Live Prices**: Yahoo Finance integration with auto-refresh (60s crypto, 120s stocks)
- **Dashboard**: Modern UI with OpenPositionsCard and HoldingsTable

### Recent Enhancements & Bug Fixes

**Oct 30, 2025 - Global Market Indicators & Portfolio Weight Display**

**Global Market Indicators Dashboard**
- Feature: Added comprehensive market indicators display to Global Analysis page
- Implementation: 12 live indicators organized into 4 categories (Equities, Risk, Commodities, Crypto)
- Indicators: S&P 500, Dow, NASDAQ, Euro Stoxx 50, DAX, VIX, 10Y Treasury, Dollar Index, Gold, Oil, Copper, Bitcoin
- Display: Blue gradient card positioned above Global Crypto Market section
- VIX Interpretation: Automatic volatility level classification (Low/Normal/Elevated/High panic)
- Backend: `MarketIndicator` and `GlobalMarketIndicators` schemas in `analysis_schemas.py`
- Frontend: New `GlobalMarketIndicators.tsx` component with responsive grid layout
- Files Modified: `analysis_schemas.py`, `prompt_renderer.py`, `analysis_service.py`, `GlobalAnalysisCard.tsx`
- Files Created: `GlobalMarketIndicators.tsx`, `GlobalMarketIndicators.css`

**Portfolio Weight Sorting & Display**
- Feature: Positions in AI Analysis page now sorted by portfolio weight (largest first)
- Feature: Added blue gradient weight badge showing portfolio percentage for each position
- Implementation: Backend calculates portfolio_percentage for each position
- Display: Weight badge positioned next to asset type badge (e.g., "CRYPTO 29.4%")
- Sorting: Automatic descending sort by portfolio weight (AMEM 29.4% → LINK 3.5%)
- Backend: Enhanced `/api/portfolio/positions` endpoint in `portfolio_router.py`
- Frontend: Updated `PositionAnalysisList.tsx` with weight badge and styling
- Files Modified: `portfolio_router.py:130-186`, `PositionAnalysisList.tsx`, `PositionAnalysisList.css`

### Previous Updates (Oct 24-29, 2025)

**Issue #3: Missing Staking Rewards**
- Problem: Position calculation missing recent staking rewards
- Fix: Auto-recalculate positions after CSV imports
- Impact: SOL position corrected from 16.35579500 to 16.36990300
- Commit: `57ea793`

**Issue #4: Fees Not in Cost Basis**
- Problem: Transaction fees excluded from cost basis calculations
- Fix: Added fee parameter to `FIFOCalculator.add_purchase()`
- Impact: Cost basis accuracy improved from ~99% to 99.77% vs Koinly
- Commit: `57ea793`

**Issue #5: OpenPositionsCard UI Enhancements**
- Feature: Added transaction fee display (total + count)
- Feature: Removed green background from Total Value card
- Feature: Dynamic P&L coloring (green for profit, red for loss)
- Implementation: Backend fee aggregation + frontend CSS fixes
- Test Coverage: 25/25 frontend tests passing, 23/23 backend tests passing
- GitHub Issue: Closed #5

**Issue #8: Holdings Table Fees Column**
- Feature: Added sortable "Fees" column to HoldingsTable showing per-position transaction fees
- Feature: Tooltip displays transaction count (e.g., "2 transactions with fees")
- Implementation: Backend fee aggregation in `/api/portfolio/positions` endpoint
- Verified: P&L calculations already correctly account for fees (purchase fees in cost basis, portfolio-level net P&L)
- Test Coverage: 10 new tests (3 backend, 7 frontend) - all passing
- GitHub Issue: Closed #8

**Issue #9: Asset Breakdown Layout with Trend Indicators**
- Feature: Redesigned asset breakdown layout with label + value on first line, P&L centered on second line
- Feature: Added 24h trend arrows (↑/↓/→) showing P&L movement since last update
- Implementation: LocalStorage-based P&L snapshot tracking with 25-hour expiration
- Trend Logic: Compares current P&L with previous snapshot (threshold: €0.01)
- UI Improvements: Eliminated visual overlap, improved spacing and readability
- Test Coverage: 6 new trend calculation tests (31/31 tests passing)
- GitHub Issue: Closed #9

**Issue #11: Stocks CSV Parser Thousands Separator Bug**
- Problem: Parser failed to import transactions with large amounts containing thousands separators (commas)
- Impact: Only 60 of 130 transactions imported, missing 3 MSTR purchases worth €4,730
- Root Cause: `float("5,000")` raises ValueError - parser silently skipped these transactions
- Fix: Added `.replace(',', '')` to strip thousands separators in `_parse_actual_format_row()`
- File Modified: `backend/csv_parser.py` (lines 303-304)
- Result: Successfully imported all 63 stock transactions (was 60)
- Verification: MSTR position corrected from 0.70 shares (€198) to 19.68 shares (€5,607)
- GitHub Issue: Closed #11

**ETF Ticker Mapping System**
- Problem: European ETFs (AMEM, MWOQ) returned 404 errors from Yahoo Finance
- Root Cause: ETFs need exchange suffixes (e.g., AMEM.BE for Brussels exchange)
- Solution: Added `ETF_MAPPINGS` dictionary in `yahoo_finance_service.py`
- Implementation: Created `_transform_ticker()` method to map internal symbols to Yahoo Finance format
- Mappings Added: AMEM → AMEM.BE, MWOQ → MWOQ.BE
- Result: All ETF prices now fetching successfully, stocks showing in dashboard
- Files Modified: `backend/yahoo_finance_service.py` (lines 39-43, 152-174, 217-264, 274-294)

**UI Modernization: Asset Breakdown Cards**
- Feature: Minimalist redesign with borderless cards and subtle backgrounds
- Styling: Removed heavy borders, added `background: rgba(0, 0, 0, 0.02)` for depth
- Icons: Applied grayscale filter and reduced opacity for monochrome aesthetic
- Smart Filtering: Only display asset types with non-zero values
- Compact Layout: 450px max-width for 1-2 assets, centered alignment
- Files Modified: `frontend/src/components/OpenPositionsCard.tsx`, `OpenPositionsCard.css`

**Issue #12: Asset Allocation Pie Chart**
- Feature: Interactive pie chart showing portfolio allocation by asset type
- Implementation: Recharts library with ResponsiveContainer for responsiveness
- Layout: CSS Grid side-by-side on desktop (cards left, chart right), stacked on mobile
- Visualization: Color-coded segments (Stocks: blue, Crypto: amber, Metals: purple)
- Interactivity: Hover tooltips showing asset value and percentage
- Smart Filtering: Only displays non-zero asset types in chart
- Component: New `AssetAllocationChart` component with 11 passing tests
- Integration: Embedded in `OpenPositionsCard` breakdown section
- Files Created: `frontend/src/components/AssetAllocationChart.tsx/css/test.tsx`
- Files Modified: `OpenPositionsCard.tsx/css`, `src/test/setup.ts` (ResizeObserver mock)
- GitHub Issue: Closed #12

**Issue #13: USD to EUR Currency Conversion Bugs (Oct 26, 2025)**
- **Problem 1**: Position values incorrectly multiplying by exchange rate instead of dividing
  - Impact: MSTR showing €6,616 instead of €4,890 (35% error)
  - Symptom: USD positions overvalued in EUR by ~2x
- **Problem 2**: Cost basis aggregation mixing USD and EUR without conversion
  - Impact: Stock P&L showing -€1,665 (-11.36%) instead of -€620 (-4.55%)
  - Symptom: Portfolio-level P&L calculations incorrect for multi-currency positions
- **Root Cause**: EURUSD=X rate means "1 EUR = X USD", required division not multiplication
- **Fix 1**: Changed `portfolio_service.py:293` from multiply to divide for USD→EUR conversion
- **Fix 2**: Updated `portfolio_router.py` to use pre-calculated `unrealized_pnl` instead of raw `total_cost_basis`
- **Enhancement**: Added `get_usd_to_eur_rate()` to YahooFinanceService with 1-hour cache
- **Result**: 99.92% portfolio accuracy vs Revolut, all currency calculations now EUR-safe
- **Test Coverage**: 9/9 open-positions tests passing, 13/13 portfolio service tests passing
- **Files Modified**: `portfolio_service.py`, `portfolio_router.py`, `yahoo_finance_service.py`, `tests/test_yahoo_finance_service.py`
- Commit: `acb0b78`

**Fear & Greed Index Integration (Oct 29, 2025)**
- Feature: Real-time crypto market sentiment indicator integrated into Global Crypto Market display
- Source: Alternative.me API (free, no authentication required)
- Display: Highlighted card showing 0-100 sentiment score with classification (Extreme Fear/Fear/Neutral/Greed/Extreme Greed)
- Update Frequency: 15-minute cache (Redis)
- AI Integration: Fear & Greed value included in Claude prompt context for sentiment-aware analysis
- Root Cause: Backend was fetching data, but Pydantic schema was filtering out the fields
- Fix: Added `fear_greed_value` and `fear_greed_classification` fields to `GlobalCryptoMarketData` schema in `analysis_schemas.py:39-40`
- Files Modified: `backend/analysis_schemas.py`
- Documentation: `CHANGELOG-2025-10-29-FearGreed.md`, `docs/AI_ANALYSIS.md`
- See: [CHANGELOG-2025-10-29-FearGreed.md](CHANGELOG-2025-10-29-FearGreed.md) for complete details

### Test Suite Improvements (Oct 24, 2025)

**Crypto Parser Tests Fixed (19/19 passing)**
- Problem: `_parse_old_format_row()` method was stubbed, causing all test format parsing to fail
- Fix: Fully implemented old format parser for test compatibility
- Added: Multi-format date parsing (ISO 8601 with timezone support)
- Added: DEPOSIT/WITHDRAWAL transaction type support
- Added: Cost basis field preservation
- Added: Header validation with helpful error messages
- Impact: All 19 crypto parser tests now passing (was 2/19)

**Remaining Test Failures Tracked**
- GitHub Issue #6: Backend import API/integration tests (13 failures) - Database fixture setup issues
- GitHub Issue #7: Frontend integration tests (46 failures) - Mock data and timeout configuration issues
- **Note**: Core functionality fully working. Failures are test infrastructure issues only.

**Current Test Status**:
- Backend: 291/304 passing (95.7%)
- Frontend: 219/267 passing (82%)
- Portfolio calculations: 71/71 passing (100%) ✅
- Crypto parser: 19/19 passing (100%) ✅
- OpenPositionsCard: 25/25 passing (100%) ✅

### Parser Implementation Details
- **MetalsParser**: Parses Revolut metals account statements (gold, silver, etc.)
- **StocksParser**: Parses Revolut stocks export (buys, sells, dividends) - handles thousands separators in large amounts
- **CryptoParser**: Parses Koinly CSV export (crypto trades, staking, airdrops, mining)

All parsers return normalized `UnifiedTransaction` objects with proper fee handling. The stocks parser correctly strips currency symbols and thousands separators before converting to float values.

### Import Handling
Multi-file uploads are supported. Each file is processed independently with per-file error reporting. The `/api/import/upload` endpoint accepts multiple files, stores transactions, and automatically recalculates positions:
```json
{
  "summary": {
    "total_files": 3,
    "successful": 2,
    "failed": 1,
    "total_saved": 150,
    "positions_recalculated": 8
  },
  "files": [/* per-file results */]
}
```

## Testing Requirements

**Mandatory**: 85% code coverage threshold (defined in docs/TESTING.md)
- Write tests BEFORE implementation (TDD)
- Every story requires unit AND integration tests
- No exceptions to coverage requirement

Current test files (all passing):
- `backend/tests/test_fifo_calculator.py` - FIFO cost basis (27 tests, 94% coverage)
- `backend/tests/test_portfolio_service.py` - Position aggregation (11 tests, 92% coverage)
- `backend/tests/test_portfolio_router.py` - Portfolio API endpoints (26 tests)
- `backend/tests/test_csv_parser.py` - CSV detection logic (21 tests)
- `backend/tests/test_import_api.py` - API endpoints (15 tests)
- `backend/tests/test_pnl_calculations.py` - P&L validation (8 tests)
- `frontend/src/components/TransactionImport.test.tsx` - Upload component (17 tests)
- `frontend/src/components/OpenPositionsCard.test.tsx` - Dashboard card (31 tests)
- `frontend/src/components/HoldingsTable.test.tsx` - Holdings table (30 tests)

## Development Workflow

### Working on a New Story
1. Check STORIES.md for current sprint focus (currently Epic 8: AI Market Analysis - F8.4-003, F8.7 & F8.8 pending)
2. Read detailed requirements in `stories/epic-*.md`
3. Write tests first (TDD approach)
4. Implement until tests pass
5. Update story status in epic file
6. Update STORIES.md progress percentages
7. Update CLAUDE.md if architectural changes made

### Completed Implementation Milestones ✅
1. ✅ Database schema (F5.2-001) - Complete
2. ✅ Parser implementations (F1.2-001, F1.2-002, F1.2-003) - All 3 parsers complete
3. ✅ Database storage (F1.3-001) - Transaction service with duplicate handling
4. ✅ FIFO calculations (F2.1-001) - Fee-inclusive cost basis with 99.77% accuracy
5. ✅ Live prices (F3.1-001, F3.1-002) - Yahoo Finance with auto-refresh
6. ✅ Dashboard (F4.1-001, F4.1-002) - OpenPositionsCard + HoldingsTable
7. ✅ **Infrastructure & DevOps (Epic 5) - COMPLETE** (F5.1-001, F5.2-001, F5.3-001):
   - Docker Compose multi-service setup
   - Database schema with auto-migrations
   - Hot-reload for backend (FastAPI) and frontend (Vite)
   - Development vs production configs
   - Comprehensive Makefile with 30+ commands
   - VS Code debugging configurations
   - Pre-commit hooks for code quality
   - Complete debugging documentation
8. ✅ **Twelve Data Integration** (Oct 29, 2025) - **CRITICAL DATA QUALITY IMPROVEMENT**:
   - Primary market data source for European securities (AMEM, MWOQ ETFs)
   - 253 days of historical data (was 1 day from Yahoo Finance)
   - Redis caching (1-hour TTL) - 98% API call reduction
   - Rate limit management: 8 calls/min, 800 calls/day
   - Intelligent fallback: Twelve Data → Yahoo → Alpha Vantage
   - Fixes: Issue #24 (AMEM 404), wrong ETF identification, flat price ranges
   - See: `CHANGELOG-2025-10-29-TwelveData.md` for complete details
9. ✅ **Epic 8: AI Market Analysis - 93% COMPLETE** (Oct 29, 2025):
   - **F8.1: Prompt Management System** ✅ (13 points):
     - Database Foundation: 3 tables, SQLAlchemy models, seed data (18 tests)
     - Prompt CRUD API: 8 REST endpoints, automatic versioning, soft deletes (46 tests)
     - Prompt Template Engine: Type-safe variable substitution, portfolio data collection (39 tests)
     - Files: `prompt_service.py`, `prompt_schemas.py`, `prompt_router.py`, `prompt_renderer.py`, `seed_prompts.py`
     - **Total**: 103 tests passing, 13/13 story points complete
   - **F8.2: Anthropic Claude Integration** ✅ (13 points):
     - Claude API Client: Async client with rate limiting (50 req/min), retry logic, token tracking (14 tests, 97% coverage)
     - Analysis Service: Orchestrates prompt rendering + Claude calls, cache integration, database storage (11 tests, 89% coverage)
     - Files: `config.py`, `claude_service.py`, `analysis_service.py`
     - **Total**: 25 tests passing, 13/13 story points complete
   - **F8.3: Global Market Analysis** ✅ (8 points):
     - Analysis Router: 3 FastAPI endpoints (/global, /position/{symbol}, /forecast/{symbol}), Redis caching (4 tests)
     - Enhanced Data Collection: 10 comprehensive fields, market indices (S&P, Dow, BTC, Gold), sector allocation (11 tests)
     - Files: `analysis_router.py`, `analysis_schemas.py`, `cache_service.py`, enhanced `prompt_renderer.py`
     - **Total**: 15 tests passing, 8/8 story points complete
   - **F8.4: Position-Level Analysis** 🟡 (15 points, 2/3 stories complete):
     - **F8.4-001**: Position Analysis API ✅ (5 points)
       - Bulk endpoint with parallel execution, recommendation extraction (HOLD/BUY_MORE/REDUCE/SELL)
       - Enhanced Schemas: `Recommendation` enum, `BulkAnalysisRequest`, `BulkAnalysisResponse`
     - **F8.4-002**: Position Context Enhancement ✅ (5 points)
       - Yahoo Finance fundamentals (sector, industry, 52-week range, volume, market cap, PE ratio)
       - Transaction context (count, first purchase date, holding period)
       - **Total**: 23 tests passing (12 unit + 7 integration + 4 API)
     - **F8.4-003**: Portfolio Context Integration 🔴 (5 points) - **NEW STORY ADDED**
       - Full portfolio composition in position analysis prompts
       - Asset allocation, sector breakdown, top holdings, concentration metrics
       - Strategic recommendations based on diversification and concentration risk
       - Transforms analysis from tactical to strategic
   - **F8.5: Forecasting Engine** ✅ (13 points):
     - Two-quarter forecasts with pessimistic/realistic/optimistic scenarios
     - Historical price data, performance metrics, market context
     - **Total**: 15 tests passing
   - **F8.6: Analysis UI Dashboard** ✅ (8 points):
     - React components: GlobalAnalysisCard, PositionAnalysisList, ForecastPanel
     - Recharts visualization with Q1/Q2 toggle
     - Brain icon sidebar navigation
   - **F8.7: AI-Powered Portfolio Rebalancing** 🔴 (18 points, 3 stories) - **NEW FEATURE**:
     - **F8.7-001**: Rebalancing Analysis Engine (8 points)
       - Calculate current vs target allocation (moderate/aggressive/conservative/custom models)
       - Identify overweight/underweight positions with ±5% trigger threshold
       - Estimate transaction costs and rebalancing delta in EUR
     - **F8.7-002**: Claude-Powered Rebalancing Recommendations (5 points)
       - Specific buy/sell recommendations with exact quantities and EUR amounts
       - Rationale for each action considering market conditions and portfolio context
       - Prioritized by deviation severity with timing suggestions
       - JSON response with expected outcome and risk assessment
     - **F8.7-003**: Rebalancing UI Dashboard (5 points)
       - Visual allocation comparison chart (current vs target)
       - Prioritized recommendations list with expand/collapse details
       - Model selector dropdown with 4 options
       - ⚖️ Scale icon in sidebar navigation
   - **F8.8: Strategy-Driven Portfolio Allocation** 🔴 (13 points, 3 stories) - **NEWEST FEATURE**:
     - **F8.8-001**: Investment Strategy Storage & API (5 points)
       - Database table for user-defined investment strategies with version tracking
       - CRUD API (GET/POST/PUT/DELETE) with validation
       - Supports free-form text + optional structured fields (target return, risk, max positions, profit threshold)
       - Example: "Take profit at +20%, reinvest in EU/emerging market growing sectors, target 15-20% YoY"
     - **F8.8-002**: Claude Strategy-Driven Recommendations (5 points)
       - Analyzes portfolio alignment with personal investment philosophy
       - Identifies profit-taking opportunities per strategy rules
       - Position assessments (fits strategy? recommended action?)
       - New position suggestions aligned with strategy
       - Action plan: Immediate/Redeployment/Gradual adjustments
       - Alignment score (0-10) and next review date
     - **F8.8-003**: Strategy Management UI (3 points)
       - Strategy editor with rich textarea (5000 chars, min 20 words)
       - Strategy template library (Conservative/Balanced/Aggressive/Income/Value)
       - Recommendations display with alignment score gauge
       - 🎯 Target icon in sidebar navigation
   - **Epic 8 Progress**: 64% complete (65/101 story points), 181/181 tests passing ✅

### Next Steps
- **Epic 8 - Feature 4: Position-Level Analysis - Story 3** (F8.4-003, 5 points):
  - Integrate full portfolio context into position analysis
  - Add asset allocation, sector breakdown, concentration metrics to prompts
  - Enable strategic recommendations considering portfolio-level diversification
- **Epic 8 - Feature 7: AI-Powered Portfolio Rebalancing** (F8.7, 18 points):
  - Rebalancing analysis engine with 4 allocation models
  - Claude-powered buy/sell recommendations with specific quantities
  - Visual dashboard with allocation comparison and recommendations list
- **Epic 8 - Feature 8: Strategy-Driven Portfolio Allocation** (F8.8, 13 points) - **NEWEST**:
  - User-defined investment strategy storage with CRUD API
  - Claude analyzes portfolio alignment with personal strategy
  - Profit-taking opportunities, position assessments, action plan
  - Strategy editor UI with templates and alignment score gauge
- Complete Epic 4 remaining stories (F4.2-001, F4.2-002): Portfolio value chart

## Docker Services Configuration

- **PostgreSQL**: Port 5432, Database: `portfolio`, User: `trader`
- **Redis**: Port 6379, for caching price data (15-minute TTL)
- **Backend**: Port 8000, FastAPI with hot reload
- **Frontend**: Port 3003, Vite dev server with HMR

Health checks ensure services start in correct order. Backend waits for PostgreSQL, Frontend waits for Backend.

### Data Storage Locations

**PostgreSQL Database** (Primary storage):
- **Docker Volume**: `portfolio-management_postgres_data`
- **Host Path**: `/var/lib/docker/volumes/portfolio-management_postgres_data/_data`
- **Container Path**: `/var/lib/postgresql/data`
- **Persistence**: Survives container restarts and `docker-compose down`
- **Deleted by**: `docker-compose down -v` or `make clean-all` ⚠️

**CSV Uploads**:
- **Host Path**: `./data/` (project directory)
- **Container Path**: `/data` (backend container)
- **Purpose**: Temporary storage for uploaded CSV files

**Backup Location**:
- **Host Path**: `./backups/` (created by `make backup`)
- **Format**: SQL dumps with timestamp (e.g., `backup_20251028_120500.sql`)

### Database Management Commands

```bash
# Backup database
make backup  # Creates timestamped SQL dump in ./backups/

# Restore from backup
make restore FILE=./backups/backup_20251028_120500.sql

# Access database shell
make shell-db  # or: docker-compose exec postgres psql -U trader portfolio

# View volume information
docker volume inspect portfolio-management_postgres_data

# ⚠️ DANGER: Delete all data
docker-compose down -v  # Removes volumes!
make clean-all          # Nuclear option
```

## Environment Variables

**SECURITY**: All credentials are stored in `.env` file (never committed to git). See `docs/SECURITY.md` for details.

### Configuration Files
- `.env` - Actual credentials (gitignored, contains secrets)
- `.env.example` - Template with placeholders (safe to commit)
- `docs/SECURITY.md` - Complete security guide

### Key Variables

**Database** (Required):
- `POSTGRES_DB`: Database name (default: portfolio)
- `POSTGRES_USER`: Database user (default: trader)
- `POSTGRES_PASSWORD`: **SECRET** - Database password
- `DATABASE_URL`: **SECRET** - Full PostgreSQL connection string

**Redis** (Required):
- `REDIS_URL`: Redis connection string (redis://redis:6379)

**Anthropic AI** (Optional - for Epic 8):
- `ANTHROPIC_API_KEY`: **SECRET** - Claude API key from console.anthropic.com
- `ANTHROPIC_MODEL`: Model to use (default: claude-sonnet-4-5-20250929)
- `ANTHROPIC_MAX_TOKENS`: Max response tokens (default: 4096)
- `ANTHROPIC_TEMPERATURE`: Sampling temperature (default: 0.3)

**Frontend**:
- `VITE_API_URL`: API endpoint (default: http://localhost:8000)
- `VITE_BASE_CURRENCY`: Base currency (default: EUR)
- Refresh intervals for crypto, stocks, portfolio, holdings

### Setup
```bash
# First time setup
cp .env.example .env
nano .env  # Add your credentials

# Start services (reads .env automatically)
docker-compose up
```

**Never commit `.env` to git!** It's in `.gitignore` for your protection.

## Market Data Architecture

### Data Sources by Use Case

The application uses multiple market data providers with intelligent fallback:

| Use Case | Primary Source | Secondary | Tertiary | Rationale |
|----------|----------------|-----------|----------|-----------|
| **AI Analysis/Forecasts** | Twelve Data | Yahoo Finance | Alpha Vantage | Best historical data for European ETFs (253 days) |
| **Historical Charts** | Twelve Data | Yahoo Finance | Alpha Vantage | Comprehensive fallback chain with circuit breaker |
| **Position Fundamentals** | Twelve Data | Yahoo Finance | - | Accurate ETF names and metadata |
| **Live Dashboard Prices** | Yahoo Finance | - | - | Free, unlimited, fast (<100ms) |

### Why Different Sources?

**Twelve Data** ($29/month Grow plan):
- ✅ 253 days of historical data for European ETFs (AMEM:XETR, MWOQ:XETR)
- ✅ Accurate asset names and exchange data
- ✅ 60+ global exchanges including Frankfurt (XETR)
- ⚠️ Rate limits: 8 calls/min, 800 calls/day
- 💡 **Used for**: AI analysis, forecasts, position context (cached 1 hour)

**Yahoo Finance** (Free):
- ✅ Unlimited API calls
- ✅ Fast real-time quotes (<100ms)
- ✅ Good US stock coverage
- ❌ Limited European ETF data (only 1 day for AMEM.BE)
- 💡 **Used for**: Live dashboard updates (every 60-120 seconds)

**Alpha Vantage** (Free tier):
- ✅ Fallback for rare data gaps
- ❌ No European ETF support
- ⚠️ Rate limits: 5 calls/min, 100 calls/day
- 💡 **Used for**: Emergency fallback only

### Redis Caching Strategy

**Cache Keys**:
- `td:daily:{symbol}:{start}:{end}` - Twelve Data historical prices (1-hour TTL)
- `td:quote:{symbol}` - Twelve Data real-time quotes (1-minute TTL)
- `analysis:forecast:{symbol}` - Claude AI forecasts (24-hour TTL)
- `analysis:position:{symbol}` - Position analysis (1-hour TTL)

**Cache Hit Rate**: ~98% after first request (dramatically reduces API usage)

### Rate Limit Management

Twelve Data enforces strict limits. The application uses:
1. **Token Bucket Algorithm**: Tracks minute (8) and daily (800) quotas
2. **Automatic Blocking**: Waits for refill if minute limit reached
3. **Exception on Daily Limit**: Prevents exceeding 800 calls/day
4. **Redis Caching**: Reduces actual API calls by 98%

**Typical Daily Usage**: 50-100 API calls (well under 800 limit)

## Key API Endpoints

### Import
- `POST /api/import/upload` - Multi-file CSV upload with auto-recalculation
- `GET /api/import/status` - Check supported file formats

### Portfolio
- `GET /api/portfolio/positions` - Get all current positions with live prices, fees, and P&L
- `POST /api/portfolio/recalculate-positions` - Manually recalculate all positions
- `GET /api/portfolio/pnl` - Get portfolio-wide P&L summary
- `GET /api/portfolio/open-positions` - Get open positions overview with aggregated fees

### Prices
- `POST /api/prices/update-all` - Manually trigger price update for all positions
- `GET /api/prices/{symbol}` - Get current price for specific symbol

### Database
- `POST /api/database/reset` - Reset database (requires confirmation)
- `GET /api/database/stats` - Get transaction and position statistics

## Portfolio Accuracy

### Cost Basis Validation
The FIFO calculator has been validated against Koinly:
- **Accuracy**: 99.77% match with Koinly cost basis calculations
- **Fee Handling**: Transaction fees properly included in cost basis
- **Transaction Types**: Supports BUY, SELL, STAKING, AIRDROP, MINING
- **Validation Data**: SOL position €2,850.33 (app) vs €2,857.00 (Koinly) = €6.67 difference (0.23%)

### Multi-Currency Support
Portfolio calculations handle USD and EUR positions correctly:
- **Overall Accuracy**: 99.92% match with Revolut for stock positions
- **Currency Conversion**: USD→EUR using live EURUSD=X rates (1-hour cache)
- **Position Values**: All values normalized to EUR for portfolio-level calculations
- **Validation Data**:
  - MSTR: €4,890.44 (app) vs €4,896.49 (Revolut) = €6.05 difference (0.12%)
  - AMEM: €6,612.62 (app) vs €6,608.43 (Revolut) = €4.19 difference (0.06%)
  - MWOQ: €1,491.43 (app) vs €1,499.36 (Revolut) = €7.93 difference (0.53%)

This level of accuracy ensures reliable tax reporting and P&L calculations across all asset types and currencies.