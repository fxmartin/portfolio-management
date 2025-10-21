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

Stories are organized into 5 major epics, each with its own detailed documentation:

1. **[Epic 1: Transaction Import & Management](./stories/epic-01-transaction-import.md)** - CSV upload and parsing
2. **[Epic 2: Portfolio Calculation Engine](./stories/epic-02-portfolio-calculation.md)** - FIFO calculations and P&L
3. **[Epic 3: Live Market Data Integration](./stories/epic-03-live-market-data.md)** - Yahoo Finance and caching
4. **[Epic 4: Portfolio Visualization](./stories/epic-04-portfolio-visualization.md)** - Dashboard and charts
5. **[Epic 5: Infrastructure & DevOps](./stories/epic-05-infrastructure.md)** - Docker and development setup

## Overall Progress Tracking

### Epic Status Overview
| Epic | Stories | Points | Status | Progress | Details |
|------|---------|--------|--------|----------|---------|
| [Epic 1: Transaction Import](./stories/epic-01-transaction-import.md) | 8 | 31 | 🟡 In Progress | 81% (25/31 pts) | CSV parsing & storage |
| [Epic 2: Portfolio Calculation](./stories/epic-02-portfolio-calculation.md) | 5 | 26 | 🔴 Not Started | 0% | FIFO, P&L, currency |
| [Epic 3: Live Market Data](./stories/epic-03-live-market-data.md) | 4 | 16 | 🔴 Not Started | 0% | Yahoo Finance, Redis |
| [Epic 4: Portfolio Visualization](./stories/epic-04-portfolio-visualization.md) | 4 | 19 | 🔴 Not Started | 0% | Dashboard, charts |
| [Epic 5: Infrastructure](./stories/epic-05-infrastructure.md) | 3 | 13 | 🟡 In Progress | 85% (11/13 pts) | Docker, database |
| **Total** | **24** | **105** | **In Progress** | **~33%** (35/105 pts) | |

### Current Sprint Focus
**Active Epic**: Transaction Import (Epic 1)
**Completed Stories**:
- F1.1-001 & F1.1-002 - Upload Component ✅
- F1.2-001, F1.2-002, F1.2-003 - All Parsers Complete ✅
- F1.3-001 - Store Transactions in Database ✅
**Next Stories**:
- F1.3-002 - Database Reset Functionality
- F1.3-003 - Database Statistics Dashboard (NEW)
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
- **Features**: CSV upload, Three-parser system (Metals, Stocks, Crypto), transaction storage
- **Key Stories**: 7 stories, 28 points
- **Status**: 🟡 In Progress (71% complete - F1.1 and F1.2 features complete)

### [Epic 2: Portfolio Calculation Engine](./stories/epic-02-portfolio-calculation.md)
- **Goal**: Calculate FIFO cost basis and P&L
- **Features**: FIFO calculator, position aggregation, P&L calculations, currency conversion
- **Key Stories**: 5 stories, 26 points
- **Status**: 🔴 Not Started

### [Epic 3: Live Market Data Integration](./stories/epic-03-live-market-data.md)
- **Goal**: Real-time prices from Yahoo Finance
- **Features**: Yahoo Finance integration, Redis caching, auto-refresh
- **Key Stories**: 4 stories, 16 points
- **Status**: 🔴 Not Started

### [Epic 4: Portfolio Visualization](./stories/epic-04-portfolio-visualization.md)
- **Goal**: Interactive dashboard with charts
- **Features**: Portfolio summary, holdings table, performance charts
- **Key Stories**: 4 stories, 19 points
- **Status**: 🔴 Not Started

### [Epic 5: Infrastructure & DevOps](./stories/epic-05-infrastructure.md)
- **Goal**: Docker environment with hot-reload
- **Features**: Docker Compose, database schema, development tools
- **Key Stories**: 3 stories, 13 points
- **Status**: 🟢 Mostly Complete (85% complete - F5.1-001 and F5.2-001 done)

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