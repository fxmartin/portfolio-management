# Portfolio Management Application

A personal portfolio tracker that imports Revolut transactions and displays real-time portfolio performance with live market data.

## Quick Start

```bash
# Start all services
docker-compose up

# Backend will be available at http://localhost:8000
# Frontend will be available at http://localhost:3003
```

## Documentation

Comprehensive documentation is available in the [`docs/`](./docs/) directory:

### Core Documentation
- **[AI Analysis](./docs/AI_ANALYSIS.md)** - Complete guide to AI-powered market analysis system
  - Prompt templates and data collection
  - Claude API integration with rate limiting and retries
  - Response processing and caching strategies
  - Cost tracking and optimization
  - 181 tests, 65/70 story points complete

- **[Architecture](./docs/ARCHITECTURE.md)** - System design and technical architecture
  - Service communication flows
  - Database schema and relationships
  - Component design patterns
  - Technology stack details

- **[Security](./docs/SECURITY.md)** - Security best practices and credential management
  - Environment variable management
  - API key storage and rotation
  - Database credential security
  - Secret handling guidelines

- **[Testing](./docs/TESTING.md)** - Testing strategy and requirements
  - 85% code coverage threshold (mandatory)
  - TDD approach and test types
  - Running tests and interpreting results
  - Current test suite status

- **[Debugging](./docs/DEBUGGING.md)** - Comprehensive debugging guide
  - VS Code debugging configurations
  - Docker troubleshooting
  - Database debugging
  - Common issues and solutions

### Additional Resources
- **[STORIES.md](./STORIES.md)** - Complete story breakdown and epic definitions (9 epics, 69 stories)
- **[PRD.md](./PRD.md)** - Product requirements and technical specifications
- **[CLAUDE.md](./CLAUDE.md)** - Development guidance for AI assistants

## Project Structure

```
portfolio-management/
├── backend/              # Python/FastAPI backend
├── frontend/             # React frontend
├── docs/                 # Comprehensive documentation
│   ├── AI_ANALYSIS.md    # AI analysis system guide
│   ├── ARCHITECTURE.md   # System architecture
│   ├── DEBUGGING.md      # Debugging guide
│   ├── SECURITY.md       # Security best practices
│   └── TESTING.md        # Testing requirements
├── stories/              # Epic and story definitions
├── docker-compose.yml    # Docker orchestration
├── CLAUDE.md             # AI assistant guidance
├── PRD.md                # Product requirements
├── STORIES.md            # Story overview
└── README.md             # This file
```

## Features

- **CSV Import**: Parse Revolut transaction exports (metals, stocks, crypto)
- **Live Prices**: Real-time market data via Yahoo Finance with auto-refresh
- **Portfolio Tracking**: FIFO cost basis with fee-inclusive calculations, accurate P&L
- **Dashboard**: Visualize holdings and performance with real-time updates
- **Multi-Asset Support**: Handles stocks, crypto, metals, staking rewards, airdrops, mining

## Project Metrics

**Development Time**: ~42.9 hours active development (80 commits across 10 active days)
- Current pace: 8.0 commits/day, 97% issues resolved
- Development intensity: 15.1 activities/day over 12 day span
- **Completion**: 76% (269/352 story points) - 9 epics total

*Run `python3 scripts/estimate_effort_v2.py` to see updated time estimates*

## Recent Improvements

### Critical Bug Fixes (Oct 26, 2025)
- **Issue #13**: Fixed USD to EUR currency conversion bugs
  - Problem 1: Position values multiplying by exchange rate instead of dividing (35% error)
  - Problem 2: Cost basis aggregation mixing USD and EUR without conversion
  - Impact: USD positions (MSTR) showing incorrect values and P&L calculations
  - Result: 99.92% portfolio accuracy vs Revolut, all currency calculations now EUR-safe
  - Enhancement: Added live exchange rate fetching with 1-hour cache

### Earlier Fixes (Oct 24, 2025)
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

### Getting Started
- **[Quick Start Guide](./docs/DEBUGGING.md#development-environment)** - Set up your development environment
- **[Testing Guide](./docs/TESTING.md)** - Run tests and meet coverage requirements
- **[Architecture Overview](./docs/ARCHITECTURE.md)** - Understand system design

### Requirements & Planning
- **[PRD.md](./PRD.md)** - Detailed requirements and technical specifications
- **[STORIES.md](./STORIES.md)** - Complete story breakdown and epic definitions (9 epics, 69 stories)
- **[Epic Details](./stories/)** - Individual epic files with acceptance criteria

## License

Personal project - not for commercial use