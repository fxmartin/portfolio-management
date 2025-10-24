# Portfolio Management Application

A personal portfolio tracker that imports Revolut transactions and displays real-time portfolio performance with live market data.

## Quick Start

```bash
# Start all services
docker-compose up

# Backend will be available at http://localhost:8000
# Frontend will be available at http://localhost:3003
```

## Project Structure

```
portfolio-management/
├── backend/           # Python/FastAPI backend
├── frontend/          # React frontend
├── docker-compose.yml # Docker orchestration
├── PRD.md            # Product requirements
└── README.md         # This file
```

## Features

- **CSV Import**: Parse Revolut transaction exports (metals, stocks, crypto)
- **Live Prices**: Real-time market data via Yahoo Finance with auto-refresh
- **Portfolio Tracking**: FIFO cost basis with fee-inclusive calculations, accurate P&L
- **Dashboard**: Visualize holdings and performance with real-time updates
- **Multi-Asset Support**: Handles stocks, crypto, metals, staking rewards, airdrops, mining

## Recent Improvements (Oct 24, 2025)

### Critical Bug Fixes
- **Issue #3**: Fixed missing staking rewards in position calculations
  - Impact: All STAKING, AIRDROP, and MINING transactions now properly included
  - Result: SOL position corrected from 16.35579500 to 16.36990300 (0.01410800 SOL recovered)

- **Issue #4**: Transaction fees now included in cost basis
  - Impact: Accurate tax reporting and P&L calculations
  - Method: Fees added to purchase cost basis (proper accounting methodology)
  - Result: Cost basis calculations now match Koinly within 0.23%

- **Auto-Recalculate**: Positions automatically recalculate after CSV imports
  - No manual intervention needed after uploading transactions
  - Ensures data consistency across all operations

### Test Coverage
- 27/27 FIFO calculator tests passing
- 5 new fee handling test scenarios
- Maintains 85%+ code coverage threshold

## Tech Stack

- **Backend**: Python 3.12, FastAPI, PostgreSQL, Redis
- **Frontend**: React 18, TypeScript, Vite
- **Infrastructure**: Docker, Docker Compose

## Testing Requirements

**IMPORTANT**: All stories must include comprehensive testing with the following principles:

- **Minimum Coverage Threshold**: 85% code coverage for all modules
- **Test Types Required**:
  - Unit tests (required for all business logic)
  - Integration tests (required for API endpoints and database operations)
  - End-to-end tests (required for critical user flows)
- **TDD Approach**: Tests must be written before implementation code
- **Definition of Done**: No story is considered complete without passing tests meeting the 85% threshold

## Development

Check the [PRD.md](./PRD.md) for detailed requirements and technical specifications.
See [STORIES.md](./STORIES.md) for the complete story breakdown and epic definitions.

## License

Personal project - not for commercial use