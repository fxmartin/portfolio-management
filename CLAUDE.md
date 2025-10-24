# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Portfolio management application for tracking stocks, metals, and cryptocurrency investments. Imports transactions from Revolut (metals & stocks) and Koinly (crypto) CSV exports, calculates FIFO cost basis with fee-inclusive calculations, and displays real-time portfolio performance with live market data.

**Current Status**: ~84% complete (104/123 story points) - All core features implemented. Transaction import, FIFO calculations, live prices, and dashboard visualization complete. Cost basis calculations validated against Koinly at 99.77% accuracy.

## Essential Commands

### Development Environment
```bash
# Start all services (PostgreSQL, Redis, Backend, Frontend)
docker-compose up

# Start with rebuild (after dependency changes)
docker-compose up --build

# Stop all services
docker-compose down

# Reset everything including volumes
docker-compose down -v
```

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

### Recent Critical Bug Fixes (Oct 24, 2025)

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

### Parser Implementation Details
- **MetalsParser**: Parses Revolut metals account statements (gold, silver, etc.)
- **StocksParser**: Parses Revolut stocks export (buys, sells, dividends)
- **CryptoParser**: Parses Koinly CSV export (crypto trades, staking, airdrops, mining)

All parsers return normalized `UnifiedTransaction` objects with proper fee handling.

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

**Mandatory**: 85% code coverage threshold (defined in TESTING.md)
- Write tests BEFORE implementation (TDD)
- Every story requires unit AND integration tests
- No exceptions to coverage requirement

Current test files (all passing):
- `backend/tests/test_fifo_calculator.py` - FIFO cost basis (27 tests, 94% coverage)
- `backend/tests/test_portfolio_service.py` - Position aggregation (11 tests, 92% coverage)
- `backend/tests/test_csv_parser.py` - CSV detection logic (21 tests)
- `backend/tests/test_import_api.py` - API endpoints (15 tests)
- `backend/tests/test_pnl_calculations.py` - P&L validation (8 tests)
- `frontend/src/components/TransactionImport.test.tsx` - Upload component (17 tests)
- `frontend/src/components/OpenPositionsCard.test.tsx` - Dashboard card (8 tests)

## Development Workflow

### Working on a New Story
1. Check STORIES.md for current sprint focus (currently Epic 4: Portfolio Visualization)
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

### Next Steps
- Complete Epic 4 remaining stories (F4.2-001, F4.2-002): Portfolio value chart and asset allocation pie chart
- Complete Epic 5 remaining story (F5.3-001): Hot reload setup

## Docker Services Configuration

- **PostgreSQL**: Port 5432, Database: `portfolio`, User: `trader`
- **Redis**: Port 6379, for caching price data (15-minute TTL)
- **Backend**: Port 8000, FastAPI with hot reload
- **Frontend**: Port 3003, Vite dev server with HMR

Health checks ensure services start in correct order. Backend waits for PostgreSQL, Frontend waits for Backend.

## Environment Variables

### Frontend
- `VITE_API_URL`: API endpoint (defaults to http://localhost:8000)

### Backend
- `DATABASE_URL`: PostgreSQL connection string (postgresql://trader:profits123@postgres:5432/portfolio)
- `REDIS_URL`: Redis connection string (redis://redis:6379)
- `PYTHONUNBUFFERED`: Set to 1 for immediate log output

## Key API Endpoints

### Import
- `POST /api/import/upload` - Multi-file CSV upload with auto-recalculation
- `GET /api/import/status` - Check supported file formats

### Portfolio
- `GET /api/portfolio/positions` - Get all current positions with live prices
- `POST /api/portfolio/recalculate-positions` - Manually recalculate all positions
- `GET /api/portfolio/pnl` - Get portfolio-wide P&L summary

### Prices
- `POST /api/prices/update-all` - Manually trigger price update for all positions
- `GET /api/prices/{symbol}` - Get current price for specific symbol

### Database
- `POST /api/database/reset` - Reset database (requires confirmation)
- `GET /api/database/stats` - Get transaction and position statistics

## Cost Basis Accuracy

The FIFO calculator has been validated against Koinly:
- **Accuracy**: 99.77% match with Koinly cost basis calculations
- **Fee Handling**: Transaction fees properly included in cost basis
- **Transaction Types**: Supports BUY, SELL, STAKING, AIRDROP, MINING
- **Validation Data**: SOL position €2,850.33 (app) vs €2,857.00 (Koinly) = €6.67 difference (0.23%)

This level of accuracy ensures reliable tax reporting and P&L calculations.