# Portfolio Management Application - Product Requirements Document

## Executive Summary

Build a personal portfolio management system that imports Revolut transaction history and displays real-time portfolio performance with live market data. Primary goal: Learn full-stack development with Python/React/PostgreSQL/Redis while building something personally useful for tracking investment performance.

## Context & Strategic Rationale

### Why Now?
- Weekend learning project to understand full-stack architecture beyond CLI applications
- Revolut's built-in analytics are limited; no unified P&L view across stocks/crypto/forex
- Opportunity to work with real financial data and multiple technical components

### Learning Objectives
- Docker containerization and orchestration
- React/Python full-stack integration
- Real-time data pipelines with Redis
- Financial calculations and data visualization

### Existing Solutions Landscape
- **Revolut App**: Basic P&L, no historical charts, can't combine with other brokers
- **Portfolio Performance**: Java-based, overkill for personal use, complex setup
- **Yahoo Finance Portfolio**: No transaction import, manual entry only
- **Spreadsheets**: No real-time data without complex macros

## User Problems & Jobs-to-be-Done

### Primary User: Me (FX)
**Pain Points:**
- Revolut CSV exports are messy with mixed transaction types
- No way to see historical portfolio value over time
- Can't track cost basis and actual P&L across different assets
- No unified view of stocks + crypto + cash positions

**Current Workaround:**
- Export CSV → Manual Excel cleanup → Still no live prices → Outdated by tomorrow

**Desired Flow:**
1. Export Revolut CSV
2. Drop into app
3. Instantly see portfolio with live prices
4. Track performance over time with actual P&L

## Solution Overview

### High-Level Architecture
```
Frontend (React) ←→ Backend (Python/FastAPI) ←→ PostgreSQL
                            ↓
                     Redis (Price Cache)
                            ↓
                     Yahoo Finance API
```

### Key Capabilities
1. **CSV Import Engine**: Parse Revolut's mixed transaction format
2. **Portfolio Calculator**: FIFO cost basis, P&L, currency conversion
3. **Live Price Feed**: Yahoo Finance integration with Redis caching
4. **Visualization Dashboard**: Real-time portfolio value, historical charts

### NOT Building (v1)
- Multi-broker support (Revolut only)
- Tax reporting
- Trade execution
- Mobile app
- Multi-user/auth system
- Backtesting/strategy analysis

## Detailed Requirements

### P0 - Must Have (MVP)

#### 1. CSV Import & Parsing
- **Input**: Revolut CSV file upload via web UI
- **Processing**:
  - Parse all transaction types (BUY, SELL, DIVIDEND, CARD_PAYMENT, TOPUP, EXCHANGE)
  - Extract ticker symbols, quantities, prices, dates
  - Handle currency notation (USD, EUR, GBP)
  - Store all transactions in PostgreSQL
- **Output**: Structured transaction list with categorization

#### 2. Portfolio Calculation Engine
- **Cost Basis**: FIFO (First-In-First-Out) methodology
- **P&L Calculation**: (Current Price - Purchase Price) × Quantity
- **Currency**: Convert all to single base currency (EUR or USD - configurable)
- **Cash Tracking**: Track remaining cash from TOPUP minus purchases
- **Holdings**: Current positions with quantity and average cost

#### 3. Live Price Integration
- **Data Source**: Yahoo Finance (yfinance Python library)
- **Supported Assets**:
  - Stocks (via Yahoo ticker symbols)
  - Major cryptos (BTC-USD, ETH-USD format)
- **Caching**: Redis with 1-minute TTL
- **Update Frequency**: Pull every 60 seconds during market hours

#### 4. Basic Dashboard
- **Current Portfolio**: Table with positions, quantities, current value, P&L
- **Portfolio Value**: Single number showing total value in base currency
- **Simple Chart**: Line chart of portfolio value (daily close prices)

### P1 - Should Have (Week 2)

#### 5. Enhanced Visualization
- **Historical Performance**: Portfolio value over time (daily/weekly/monthly)
- **Asset Allocation**: Pie chart of holdings
- **P&L Timeline**: Show realized vs unrealized gains
- **Individual Asset Charts**: Click position to see price history

#### 6. Manual Transaction Entry
- **Form Fields**: Date, Type (BUY/SELL), Ticker, Quantity, Price, Currency
- **Validation**: Check ticker exists, quantity/price are positive
- **Edit/Delete**: Modify imported transactions

#### 7. Data Refresh Controls
- **Manual Refresh**: Button to force price update
- **Auto-refresh Toggle**: Enable/disable automatic updates
- **Last Updated Timestamp**: Show when prices were last fetched

### P2 - Nice to Have (Future)

#### 8. Advanced Analytics
- **Performance Metrics**: Sharpe ratio, volatility, beta
- **Comparison**: Benchmark against S&P 500
- **Dividend Tracking**: Separate dividend income view

#### 9. Export Functionality
- **PDF Reports**: Monthly/yearly statements
- **CSV Export**: Processed transactions with P&L

#### 10. Multi-broker Support
- **Import Adapters**: IBKR, Coinbase, Degiro formats
- **Format Detection**: Auto-identify CSV format

### Non-Functional Requirements

#### Performance
- CSV import: Handle 10,000 transactions in <5 seconds
- Dashboard load: <2 seconds initial load
- Price updates: <500ms for portfolio refresh

#### Reliability
- Graceful handling of Yahoo Finance API failures
- Transaction integrity: No duplicate imports
- Data persistence: All transactions in PostgreSQL

#### Development Setup
- Full Docker Compose setup
- Single command startup: `docker-compose up`
- Hot reload for both React and Python
- Seed data for testing

## Success Criteria & Metrics

### MVP Success (Week 1)
- ✓ Import actual Revolut CSV without errors
- ✓ Display current portfolio with live prices
- ✓ Calculate P&L matching manual calculations within 5%
- ✓ Docker setup works on fresh machine

### Learning Success
- ✓ Understand React state management with financial data
- ✓ Implement WebSocket or polling for real-time updates
- ✓ Design proper database schema for financial transactions
- ✓ Handle async Python with external APIs

## Implementation Plan

### Phase 1: Foundation (Day 1)
- Docker Compose setup (PostgreSQL, Redis, Python, React)
- Basic project structure
- Database schema creation
- Simple "Hello World" endpoints

### Phase 2: CSV Import (Day 2)
- Revolut CSV parser
- Transaction storage in PostgreSQL
- Basic API endpoint for file upload
- Simple React upload form

### Phase 3: Portfolio Logic (Day 3)
- FIFO cost basis calculator
- Position aggregation
- P&L calculations
- API endpoints for portfolio data

### Phase 4: Live Data (Day 4)
- Yahoo Finance integration
- Redis caching layer
- Price update mechanism
- Connect to frontend

### Phase 5: Visualization (Day 5)
- React dashboard layout
- Portfolio table component
- Basic charting with Chart.js or Recharts
- Real-time updates

## Technical Stack

### Backend
- **Language**: Python 3.12
- **Framework**: FastAPI
- **ORM**: SQLAlchemy
- **Package Manager**: uv
- **Price Data**: yfinance
- **Async**: asyncio + httpx

### Frontend
- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS
- **Charts**: Recharts or Chart.js
- **State**: Zustand or Context API
- **Build**: Vite

### Infrastructure
- **Database**: PostgreSQL 16
- **Cache**: Redis 7
- **Containerization**: Docker + Docker Compose
- **Reverse Proxy**: nginx (optional)

### Development Tools
- **API Testing**: Thunder Client / Postman
- **DB Client**: pgAdmin (in Docker)
- **Redis GUI**: RedisInsight (optional)

## Risks & Mitigation

### Technical Risks
| Risk | Impact | Mitigation |
|------|---------|------------|
| Yahoo Finance API rate limits | No live prices | Implement exponential backoff, cache aggressively |
| Revolut CSV format changes | Import fails | Version detection, flexible parser |
| Complex transaction types | Wrong P&L | Start with BUY/SELL only, add complexity gradually |
| Currency conversion accuracy | Incorrect values | Use single currency initially, document limitation |

### Learning Risks
| Risk | Impact | Mitigation |
|------|---------|------------|
| Scope creep | Never finish MVP | Strict P0 focus, park ideas in P2 |
| Over-engineering | Complexity paralysis | Start simple, refactor later |
| Perfect is enemy of good | No working version | Time-box to weekend, ship something |

## Database Schema (Draft)

```sql
-- Core tables needed
transactions (
    id, date, type, ticker, quantity,
    price, currency, fee, raw_description,
    source_file, created_at
)

positions (
    ticker, total_quantity, avg_cost_basis,
    realized_pl, unrealized_pl, last_updated
)

price_history (
    ticker, date, open, close, high, low, volume
)

portfolio_snapshots (
    date, total_value, cash_balance, positions_json
)
```

## Sample Docker Compose Structure

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: portfolio
      POSTGRES_USER: trader
      POSTGRES_PASSWORD: profits
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://trader:profits@postgres/portfolio
      REDIS_URL: redis://redis:6379
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    ports:
      - "3003:3003"
    volumes:
      - ./frontend:/app
    environment:
      VITE_API_URL: http://localhost:8000

volumes:
  postgres_data:
```

## Definition of Done

### MVP Complete When:
- [ ] Can import Revolut CSV with 100+ transactions
- [ ] Dashboard shows current portfolio value in real-time
- [ ] P&L calculations match manual verification
- [ ] Docker Compose starts everything with one command
- [ ] Basic documentation exists
- [ ] Code is in Git with meaningful commit history

---

*Remember: This is a learning project. Focus on getting something working end-to-end rather than perfecting each component. You can always iterate.*