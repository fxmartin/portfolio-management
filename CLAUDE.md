# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Portfolio management application for tracking stocks, metals, and cryptocurrency investments. Imports transactions from Revolut (metals & stocks) and Koinly (crypto) CSV exports, calculates FIFO cost basis, and displays real-time portfolio performance with live market data.

**Current Status**: ~9% complete (8/97 story points) - Multi-file CSV upload component complete, parsers need implementation.

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
4. **Database Storage**: Transactions saved to PostgreSQL (not yet implemented)
5. **FIFO Calculation**: Portfolio engine calculates positions (not yet implemented)

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

### Database Schema (F5.2-001 - Not Implemented)
The `transactions` table schema is defined in `epic-01-transaction-import.md:305-332` but not yet created. This blocks all parser implementations.

### Parser Stubs Need Implementation
- `MetalsParser.parse()` - Parse Revolut metals CSV
- `StocksParser.parse()` - Parse Revolut stocks CSV
- `CryptoParser.parse()` - Parse Koinly CSV

Each parser must return normalized transactions matching the `UnifiedTransaction` model.

### Import Handling
Multi-file uploads are supported. Each file is processed independently with per-file error reporting. The `/api/import/upload` endpoint accepts multiple files and returns:
```json
{
  "summary": { "total_files": 3, "successful": 2, "failed": 1 },
  "files": [/* per-file results */]
}
```

## Testing Requirements

**Mandatory**: 85% code coverage threshold (defined in TESTING.md)
- Write tests BEFORE implementation (TDD)
- Every story requires unit AND integration tests
- No exceptions to coverage requirement

Current test files:
- `backend/tests/test_csv_parser.py` - CSV detection logic (21 tests)
- `backend/tests/test_import_api.py` - API endpoints (15 tests)
- `frontend/src/components/TransactionImport.test.tsx` - Upload component (17 tests)

## Development Workflow

### Working on a New Story
1. Check STORIES.md for current sprint focus
2. Read detailed requirements in `stories/epic-*.md`
3. Write tests first (TDD approach)
4. Implement until tests pass
5. Update story status in epic file
6. Update STORIES.md progress percentages

### Import Flow Implementation Order
1. Database schema (F5.2-001) - Required first
2. Parser implementations (F1.2-001, F1.2-002)
3. Database storage (F1.3-001)
4. FIFO calculations (F2.1-001)
5. Live prices (F3.1-001)

## Docker Services Configuration

- **PostgreSQL**: Port 5432, Database: `portfolio_db`
- **Redis**: Port 6379, for caching price data
- **Backend**: Port 8000, FastAPI with hot reload
- **Frontend**: Port 3003, Vite dev server with HMR

Health checks ensure services start in correct order. Backend waits for PostgreSQL, Frontend waits for Backend.

## Environment Variables

Frontend expects: `VITE_API_URL` (defaults to http://localhost:8000)
Backend database URL is hardcoded in docker-compose.yml (should be moved to .env file)

## Current Blockers

1. **Database schema not implemented** - Prevents all data persistence
2. **CSV parsers are stubs** - Can't process real transaction data
3. **No portfolio calculations** - FIFO and P&L logic not built
4. **No live price integration** - Yahoo Finance connection not implemented