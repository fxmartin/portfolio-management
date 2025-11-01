# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Documentation Principles ⚠️ IMPORTANT

**Where to Document What**:
- **CLAUDE.md** (this file): Essential project information ONLY (<150 lines)
  - Project overview, essential commands, architecture patterns, key technical notes
  - Keep it concise - developers need quick reference, not a novel
- **STORIES.md**: Progress tracking and recent updates
  - Sprint progress, epic completion status, recent bug fixes, feature enhancements
  - Detailed test results, development metrics, changelog entries
- **Epic files** (stories/epic-*.md): Detailed story specifications
  - Story acceptance criteria, implementation details, test plans

**Rule of Thumb**: If it's about "what was done" or "what's next", put it in STORIES.md. If it's about "how the system works", keep it here.

## Project Overview

Portfolio management application for tracking stocks, metals, and cryptocurrency investments. Imports transactions from Revolut (metals & stocks) and Koinly (crypto) CSV exports, calculates FIFO cost basis with fee-inclusive calculations, and displays real-time portfolio performance with live market data.

**Current Status**: ~76% complete (269/352 story points) - See STORIES.md for detailed progress and recent updates.

## Essential Commands

**Start Development**: `make dev` (starts all services with hot-reload)
**Run Tests**: `make test` (backend + frontend)
**View Logs**: `make logs`
**Help**: `make help` (shows all 30+ available commands)

**Backend**: `uv add <package>` (dependencies), `uv run pytest tests/ -v` (tests)
**Frontend**: `npm install` (dependencies), `npm test` (tests)

**See Also**: `Makefile`, `docs/DEBUGGING.md`, `docs/AI_ANALYSIS.md`, `.vscode/launch.json`

## Architecture Overview

### Service Communication Flow
```
User → React (3003) → FastAPI (8000) → PostgreSQL (5432)
                                    ↓
                                 Redis (6379)
```

### CSV Processing Pipeline
Frontend detection → Backend validation → Parser (Factory pattern) → Database storage → FIFO calculation → Auto-recalculation

**File Detection**: Metals (`account-statement_*`), Stocks (UUID pattern), Crypto (`*koinly*`)

### Key Design Patterns
Factory (parser selection), Router (FastAPI modules), Component Architecture (React), Async First (all I/O)

## Critical Implementation Notes

### Parser Implementation Details
- **MetalsParser**: Parses Revolut metals account statements (gold, silver, etc.) with EUR_AMOUNT_MAPPING for accurate P&L
- **StocksParser**: Parses Revolut stocks export (buys, sells, dividends) - handles thousands separators in large amounts
- **CryptoParser**: Parses Koinly CSV export (crypto trades, staking, airdrops, mining)
- All parsers return normalized `UnifiedTransaction` objects with proper fee handling

### ETF Ticker Mapping
European ETFs need exchange suffixes for Yahoo Finance:
- `ETF_MAPPINGS` dictionary in `yahoo_finance_service.py` maps internal symbols (AMEM → AMEM.BE, MWOQ → MWOQ.BE)
- `_transform_ticker()` method handles automatic transformation

### Portfolio Accuracy Validation
- **Cost Basis**: 99.77% match with Koinly (fees included in calculations)
- **Multi-Currency**: 99.92% match with Revolut (USD→EUR using live EURUSD=X rates, 1-hour cache)
- **Transaction Types**: BUY, SELL, STAKING, AIRDROP, MINING all supported

### Import Handling
Multi-file uploads supported. The `/api/import/upload` endpoint processes files independently with per-file error reporting and automatic position recalculation.

## Testing Requirements

**Mandatory**: 85% code coverage threshold (TDD approach)
- Write tests BEFORE implementation
- Every story requires unit AND integration tests
- No exceptions to coverage requirement
- See STORIES.md for current test suite status

## Development Workflow

### Working on a New Story
1. Check STORIES.md for current sprint focus and next priorities
2. Read detailed requirements in `stories/epic-*.md`
3. Write tests first (TDD approach)
4. Implement until tests pass
5. Update story status in epic file
6. Update STORIES.md progress percentages
7. Update STORIES.md "Recent Updates" section with implementation details

## Docker Services

- **PostgreSQL**: Port 5432 (`portfolio` database, data in Docker volume)
- **Redis**: Port 6379 (caching with 15-minute TTL)
- **Backend**: Port 8000 (FastAPI with hot reload)
- **Frontend**: Port 3003 (Vite dev server with HMR)

**Data Persistence**: Database survives `docker-compose down` but is deleted by `docker-compose down -v` or `make clean-all` ⚠️
**Backup/Restore**: Use `make backup` and `make restore FILE=path/to/backup.sql`

## Environment Variables

**SECURITY**: All credentials in `.env` file (gitignored). See `docs/SECURITY.md` for complete guide.

**Key Variables**:
- Database: `POSTGRES_PASSWORD`, `DATABASE_URL` (secrets)
- Anthropic AI: `ANTHROPIC_API_KEY` (secret, optional for Epic 8)
- Redis: `REDIS_URL` (default: redis://redis:6379)
- Frontend: `VITE_API_URL`, `VITE_BASE_CURRENCY`

**Setup**: `cp .env.example .env` and add your credentials. Never commit `.env` to git!

## Market Data Architecture

**Multi-Source Strategy**: Twelve Data (primary for historical/fundamentals) → Yahoo Finance (fallback, used for live prices) → Alpha Vantage (emergency)

**Why Multiple Sources**:
- **Twelve Data**: $29/mo, 253 days European ETF history, rate limits 8/min & 800/day, used for AI analysis
- **Yahoo Finance**: Free, unlimited calls, <100ms, used for live dashboard updates (60-120s refresh)
- **Alpha Vantage**: Free fallback, 5/min & 100/day limits

**Redis Caching**: 1-hour TTL for historical data, 1-minute for quotes, 24-hour for forecasts. ~98% cache hit rate reduces API calls dramatically.

**Rate Limiting**: Token bucket algorithm tracks quotas, automatic blocking prevents exceeding limits. Typical usage: 50-100 Twelve Data calls/day (well under 800 limit).

## Key API Endpoints

**Import**: `POST /api/import/upload` (multi-file CSV with auto-recalculation)
**Portfolio**: `GET /api/portfolio/positions`, `GET /api/portfolio/pnl`, `POST /api/portfolio/recalculate-positions`
**Transactions**: `GET/POST/PUT/DELETE /api/transactions`, `POST /api/transactions/bulk`
**Analysis**: `GET /api/analysis/global`, `GET /api/analysis/position/{symbol}`, `GET /api/analysis/forecast/{symbol}`
**Prices**: `POST /api/prices/update-all`, `GET /api/prices/{symbol}`
**Database**: `POST /api/database/reset`, `GET /api/database/stats`

---

**For detailed progress tracking, recent updates, bug fixes, and development metrics, see [STORIES.md](./STORIES.md)**