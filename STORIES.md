# USER STORIES - Portfolio Management Application

## Executive Summary

This document provides a high-level overview of all user stories for the Portfolio Management Application. Detailed stories are organized by epic in separate files for better maintainability and tracking.

**Project Goal**: Build a personal portfolio tracker that imports Revolut transactions and displays real-time portfolio performance with live market data.

## Testing Requirements

**⚠️ CRITICAL**: Every story MUST include comprehensive testing to be considered complete:
- **Minimum Coverage**: 85% code coverage threshold for all modules
- **Test Types**: Unit tests AND integration tests are mandatory for every story
- **TDD Approach**: Write tests BEFORE implementation code
- **No Exceptions**: A story is NOT complete without passing tests meeting the 85% threshold

## Story Organization

Stories are organized into 6 major epics, each with its own detailed documentation:

1. **[Epic 1: Transaction Import & Management](./stories/epic-01-transaction-import.md)** - CSV upload and parsing
2. **[Epic 2: Portfolio Calculation Engine](./stories/epic-02-portfolio-calculation.md)** - FIFO calculations and P&L
3. **[Epic 3: Live Market Data Integration](./stories/epic-03-live-market-data.md)** - Yahoo Finance and caching
4. **[Epic 4: Portfolio Visualization](./stories/epic-04-portfolio-visualization.md)** - Dashboard and charts
5. **[Epic 5: Infrastructure & DevOps](./stories/epic-05-infrastructure.md)** - Docker and development setup
6. **[Epic 6: UI Modernization & Navigation](./stories/epic-06-ui-modernization.md)** - Modern sidebar and theme

## Overall Progress Tracking

### Epic Status Overview
| Epic | Stories | Points | Status | Progress | Details |
|------|---------|--------|--------|----------|---------|
| [Epic 1: Transaction Import](./stories/epic-01-transaction-import.md) | 8 | 31 | ✅ Complete | 100% (31/31 pts) | CSV parsing & storage |
| [Epic 2: Portfolio Calculation](./stories/epic-02-portfolio-calculation.md) | 5 | 26 | ✅ Complete | 100% (26/26 pts) | FIFO, P&L, currency |
| [Epic 3: Live Market Data](./stories/epic-03-live-market-data.md) | 4 | 16 | ✅ Complete | 100% (16/16 pts) | Yahoo Finance, Redis |
| [Epic 4: Portfolio Visualization](./stories/epic-04-portfolio-visualization.md) | 4 | 19 | 🟡 In Progress | 42% (8/19 pts) | Dashboard, auto-refresh |
| [Epic 5: Infrastructure](./stories/epic-05-infrastructure.md) | 3 | 13 | 🟡 In Progress | 85% (11/13 pts) | Docker, database |
| [Epic 6: UI Modernization](./stories/epic-06-ui-modernization.md) | 7 | 18 | ✅ Complete | 100% (18/18 pts) | Sidebar, tabs, theme |
| **Total** | **31** | **123** | **In Progress** | **~84%** (104/123 pts) | |

## Recent Updates (Oct 24, 2025)

### Critical Bug Fixes - Cost Basis Accuracy
- **Fixed Missing Staking Rewards in Position Calculations** (GitHub Issue #3)
  - Issue: SOL position missing 0.01410800 SOL (5 recent staking transactions)
  - Root Cause: Position calculation stopped processing before all transactions
  - Fix: Added auto-recalculation after CSV imports
  - Impact: SOL position corrected to 16.36990300 (matches Koinly exactly)
  - Test Coverage: All 27 FIFO calculator tests passing
  - Commit: `57ea793`

- **Transaction Fees Now Included in Cost Basis** (GitHub Issue #4)
  - Issue: Fees excluded from cost basis, causing understated costs and overstated gains
  - Root Cause: FIFOCalculator.add_purchase() didn't accept fee parameter
  - Fix: Fees now included in cost basis calculation: adjusted_price = (price × quantity + fee) / quantity
  - Impact: Cost basis increased by €9.23 for SOL (now €2,850.33 vs €2,841.10)
  - Accuracy: Matches Koinly within 0.23% (€2,850.33 vs €2,857.00)
  - Test Coverage: Added 5 new fee handling tests, all passing
  - Commit: `57ea793`

- **Auto-Recalculate Positions After Import**
  - Feature: Import endpoint now automatically recalculates all positions
  - Benefit: No manual intervention needed, ensures data consistency
  - Implementation: `import_router.py` calls `PortfolioService.recalculate_all_positions()`
  - Commit: `57ea793`

### Previous Updates (Oct 21, 2025)

- **Fixed Currency-Specific Prices**: Crypto prices now fetch in correct currency (EUR vs USD)
  - Issue: LINK showed $18.84 USD instead of €16.19 EUR
  - Fix: Updated Yahoo Finance service to group crypto by currency and fetch currency-specific pairs
  - Commit: `0dab98f`

- **Fixed Staking Rewards Bug** (GitHub Issue #1)
  - Issue: SOL position missing 0.17 SOL (50 staking reward transactions)
  - Root Cause: Portfolio service ignored STAKING, AIRDROP, and MINING transaction types
  - Fix: Added support for all reward transaction types in position calculations
  - Impact: SOL position now 16.355795 (was 16.186295) - matches Revolut exactly
  - Test Coverage: Added 2 comprehensive tests, all 13 portfolio service tests passing
  - Commits: `f65eefb`

- **Implemented Auto-Refresh**: Crypto prices now update every 60 seconds
  - Feature: Configurable refresh intervals via environment variables
  - Default: 60s for crypto (24/7 trading), 120s for stocks
  - UI: Shows "Auto-refresh: 1m" badge with live timestamps
  - Implementation: Fixed React hooks with useCallback to prevent stale closures
  - Commits: `5c48a58`, `c142fcf`

### Current Sprint Focus
**Active Epic**: Portfolio Visualization (Epic 4)
**Completed Epics**:
- ✅ Epic 1: Transaction Import (8 stories, 31 points) - **100% COMPLETE**
  - F1.1-001 & F1.1-002 - Upload Component ✅
  - F1.2-001, F1.2-002, F1.2-003 - All Parsers ✅
  - F1.3-001 - Store Transactions ✅
  - F1.3-002 - Database Reset ✅
  - F1.3-003 - Database Statistics ✅
- ✅ Epic 2: Portfolio Calculation (5 stories, 26 points) - **100% COMPLETE**
  - F2.1-001 - FIFO Cost Basis Calculator ✅
  - F2.2-001 - Position Aggregation ✅
  - F2.3-001 - Unrealized P&L Calculation ✅
  - F2.3-002 - Realized P&L Calculation ✅
  - F2.4-001 - Currency Conversion ✅
- ✅ Epic 3: Live Market Data (4 stories, 16 points) - **100% COMPLETE**
  - F3.1-001 - Fetch Live Stock Prices ✅
  - F3.1-002 - Fetch Cryptocurrency Prices ✅
  - F3.2-001 - Cache Price Data ✅
  - F3.3-001 - Automatic Price Refresh ✅
- ✅ Epic 6: UI Modernization (7 stories, 18 points) - **100% COMPLETE**
  - F6.1-001 - Icon-Only Sidebar ✅
  - F6.1-002 - Expandable Database Submenu ✅
  - F6.1-003 - Sidebar Tooltips ✅
  - F6.2-001 - Tab View Component ✅
  - F6.2-002 - Component Integration ✅
  - F6.3-001 - Design System ✅
  - F6.3-002 - Modern Styling ✅
- 🟡 Epic 4: Portfolio Visualization (4 stories, 19 points) - **IN PROGRESS**
  - ✅ F4.1-001 - Portfolio Summary View (3 pts) - **COMPLETE**
  - ✅ F4.1-002 - Holdings Table (5 pts) - **COMPLETE**
**Next Stories**:
- F4.2-001 - Portfolio Value Chart (8 pts)
- F4.2-002 - Asset Allocation Pie Chart (3 pts)
**Blockers**: None

## User Personas

### Primary Persona: FX (Portfolio Owner)
- **Role**: Individual investor using Revolut for stocks, crypto, and forex trading
- **Goals**: Track complete portfolio performance, understand P&L across all assets, make informed investment decisions
- **Pain Points**: Revolut's limited analytics, manual Excel calculations, no historical tracking, mixed transaction types
- **Context**: Weekend project for learning full-stack development while solving personal portfolio tracking needs

## Epic Summaries

### [Epic 1: Transaction Import & Management](./stories/epic-01-transaction-import.md)
- **Goal**: Parse Revolut CSV exports and store transactions
- **Features**: CSV upload, Three-parser system (Metals, Stocks, Crypto), transaction storage, database management
- **Key Stories**: 8 stories, 31 points
- **Status**: ✅ Complete (100% complete - All features implemented and tested)

### [Epic 2: Portfolio Calculation Engine](./stories/epic-02-portfolio-calculation.md)
- **Goal**: Calculate FIFO cost basis and P&L
- **Features**: FIFO calculator, position aggregation, P&L calculations, currency conversion
- **Key Stories**: 5 stories, 26 points
- **Status**: ✅ Complete (100% complete - All calculation features implemented with 93% test coverage)

### [Epic 3: Live Market Data Integration](./stories/epic-03-live-market-data.md)
- **Goal**: Real-time prices from Yahoo Finance
- **Features**: Yahoo Finance integration, Redis caching, auto-refresh, currency-specific price fetching
- **Key Stories**: 4 stories, 16 points
- **Status**: ✅ Complete (100% complete - All features implemented with auto-refresh and currency fixes)

### [Epic 4: Portfolio Visualization](./stories/epic-04-portfolio-visualization.md)
- **Goal**: Interactive dashboard with charts
- **Features**: Portfolio summary, holdings table, performance charts
- **Key Stories**: 4 stories, 19 points
- **Status**: 🟡 In Progress (42% complete - Dashboard feature complete)

### [Epic 5: Infrastructure & DevOps](./stories/epic-05-infrastructure.md)
- **Goal**: Docker environment with hot-reload
- **Features**: Docker Compose, database schema, development tools
- **Key Stories**: 3 stories, 13 points
- **Status**: 🟢 Mostly Complete (85% complete - F5.1-001 and F5.2-001 done)

### [Epic 6: UI Modernization & Navigation](./stories/epic-06-ui-modernization.md)
- **Goal**: Modern, professional UI with icon sidebar and tab navigation
- **Features**: Icon-only sidebar, tab-based content, clean light theme
- **Key Stories**: 7 stories, 18 points
- **Status**: ✅ Complete (100% complete - Modern UI with sidebar navigation, tab system, and design system)

## MVP Implementation Plan

### 5-Day Sprint Schedule

#### Day 1: Foundation (13 points)
**Goal**: Set up development environment and basic structure
- ✅ F5.1-001: Multi-Service Docker Setup (5 pts) - **COMPLETE**
- ✅ F5.2-001: Create Database Tables (5 pts) - **COMPLETE**
- 🟡 F5.3-001: Hot Reload Setup (3 pts) - **IN PROGRESS**

#### Day 2: CSV Import (18 points)
**Goal**: Implement Revolut CSV parsing and storage
- ✅ F1.1-001: File Upload Component (3 pts) - **COMPLETE**
- ✅ F1.1-002: Upload Status Feedback (2 pts) - **COMPLETE**
- 🔴 F1.2-001: Parse Transaction Types (5 pts)
- 🔴 F1.2-002: Extract Transaction Details (8 pts)

#### Day 3: Portfolio Logic (18 points)
**Goal**: Implement FIFO calculations and position aggregation
- 🔴 F1.3-001: Store Transactions in Database (5 pts)
- 🔴 F2.1-001: Implement FIFO Algorithm (8 pts)
- 🔴 F2.2-001: Calculate Current Holdings (5 pts)

#### Day 4: Live Data (14 points)
**Goal**: Integrate Yahoo Finance and implement caching
- 🔴 F3.1-001: Fetch Live Stock Prices (5 pts)
- 🔴 F3.1-002: Fetch Cryptocurrency Prices (3 pts)
- 🔴 F3.2-001: Cache Price Data (3 pts)
- 🔴 F2.3-001: Calculate Unrealized P&L (3 pts)

#### Day 5: Visualization (13 points)
**Goal**: Build dashboard and integrate all components
- 🔴 F2.4-001: Single Base Currency Conversion (5 pts)
- 🔴 F4.1-001: Portfolio Summary View (3 pts)
- 🔴 F4.1-002: Holdings Table (5 pts)

**Total MVP**: 76 story points across 17 stories

## How to Use This Document

### For Development
1. **Start Here**: Check the current sprint focus in the Progress Tracking section
2. **Pick a Story**: Navigate to the relevant epic file for detailed acceptance criteria
3. **Update Status**: Mark stories as complete in the epic files as you finish them

### For Planning
- **Epic Files**: Each epic file contains detailed stories with acceptance criteria
- **Dependencies**: Check story dependencies before starting work
- **Risk Assessment**: High-risk stories may need spikes or additional research

### Quick Links
- 📁 [Transaction Import Stories](./stories/epic-01-transaction-import.md)
- 📊 [Portfolio Calculation Stories](./stories/epic-02-portfolio-calculation.md)
- 📈 [Live Market Data Stories](./stories/epic-03-live-market-data.md)
- 📉 [Visualization Stories](./stories/epic-04-portfolio-visualization.md)
- 🐳 [Infrastructure Stories](./stories/epic-05-infrastructure.md)

## Story Status Legend
- 🔴 **Not Started**: Story has not been begun
- 🟡 **In Progress**: Active development
- 🟢 **Complete**: All acceptance criteria met
- ⚠️ **Blocked**: Waiting on dependency or external factor

## Next Steps

### Immediate Actions
1. Complete database schema setup (F5.2-001)
2. Finish hot reload configuration (F5.3-001)
3. Begin CSV upload component (F1.1-001)

### Post-MVP Features
After completing the MVP, consider these enhancements:
- Manual transaction entry
- Portfolio performance charts
- Advanced analytics (Sharpe ratio, volatility)
- Multi-broker support
- Export functionality

---

*For detailed user stories, acceptance criteria, and technical specifications, please refer to the individual epic files linked above.*