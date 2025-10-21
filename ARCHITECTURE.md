# Portfolio Management Application - Codebase Analysis

**Project Location**: `/Users/user/dev/portfolio-management`  
**Analysis Date**: October 21, 2025  
**Git Status**: Git repository initialized  

---

## 1. PROJECT STRUCTURE OVERVIEW

```
portfolio-management/
├── backend/                      # Python/FastAPI backend
│   ├── pyproject.toml           # Project configuration and dependencies
│   ├── uv.lock                  # Dependency lock file
│   ├── Dockerfile               # Multi-stage build (builder + runtime)
│   ├── main.py                  # FastAPI application entry point
│   ├── import_router.py         # CSV import API endpoints
│   ├── csv_parser.py            # CSV detection and parsing logic
│   ├── .venv/                   # Virtual environment
│   ├── tests/
│   │   ├── test_csv_parser.py       # 21 unit tests for CSV detection/validation
│   │   └── test_import_api.py       # 15 integration tests for API endpoints
│   └── .python-version          # Specifies Python 3.12
│
├── frontend/                     # React/TypeScript frontend
│   ├── package.json             # Node dependencies
│   ├── package-lock.json        # Lock file
│   ├── Dockerfile               # Multi-stage build
│   ├── vite.config.ts          # Vite build configuration
│   ├── vitest.config.ts        # Test runner configuration
│   ├── tsconfig.json           # TypeScript configuration
│   ├── index.html              # Entry HTML file
│   ├── src/
│   │   ├── main.tsx            # React entry point
│   │   ├── App.tsx             # Main application component
│   │   ├── App.css             # Application styling
│   │   ├── index.css           # Global styles
│   │   ├── components/
│   │   │   ├── TransactionImport.tsx      # Multi-file upload component
│   │   │   ├── TransactionImport.tsx      # Component styling
│   │   │   └── TransactionImport.test.tsx # 17 component tests
│   │   └── test/
│   │       └── setup.ts        # Test configuration
│   └── node_modules/           # Dependencies
│
├── stories/                      # Epic user stories (markdown)
│   ├── epic-01-transaction-import.md        # CSV import (partially complete)
│   ├── epic-02-portfolio-calculation.md     # FIFO & P&L (not started)
│   ├── epic-03-live-market-data.md         # Yahoo Finance integration
│   ├── epic-04-portfolio-visualization.md  # Dashboard & charts
│   └── epic-05-infrastructure.md           # Docker & database setup
│
├── data/                        # Data storage directory
├── uploads/                     # User uploaded files
├── Revolut_import_20-oct-25/   # Sample transaction data
│
├── docker-compose.yml           # Multi-service orchestration
├── README.md                    # Quick start guide
├── PRD.md                       # Detailed product requirements (326 lines)
├── TESTING.md                   # Testing standards and guidelines (260 lines)
└── STORIES.md                   # Story overview and tracking (163 lines)
```

---

## 2. TECH STACK SUMMARY

### Backend (Python)
- **Framework**: FastAPI 0.119.1
- **Language**: Python 3.12
- **Package Manager**: uv (fast, modern alternative to pip)
- **Database**: PostgreSQL 16 (via asyncpg + SQLAlchemy)
- **Cache**: Redis 7
- **Market Data**: yfinance 0.2.66
- **Server**: uvicorn 0.38.0
- **Testing**: pytest 8.4.2, pytest-asyncio 1.2.0
- **Data Processing**: pandas 2.3.3

### Frontend (React)
- **Framework**: React 18 (latest)
- **Language**: TypeScript 5.9.3
- **Build Tool**: Vite 7.1.7
- **Styling**: Tailwind CSS 4.1.15
- **Charts**: Recharts 3.3.0
- **HTTP Client**: Axios 1.12.2
- **Testing**: Vitest 3.2.4, React Testing Library 6.9.1
- **Linting**: ESLint 9.36.0

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Database**: PostgreSQL 16-alpine
- **Cache**: Redis 7-alpine
- **Language Version**: Python 3.12
- **Node Version**: Implied modern LTS (package.json uses module format)

---

## 3. KEY CONFIGURATION FILES

### docker-compose.yml
Multi-service orchestration with health checks:
- **PostgreSQL**: Port 5432, database "portfolio", user "trader"
- **Redis**: Port 6379
- **Backend**: Port 8000, depends on both db and cache
- **Frontend**: Port 3003, depends on backend
- Environment variables passed to services
- Volumes for persistence and hot-reload development

### Backend Configuration
**pyproject.toml** (uv format):
- Project version: 0.1.0
- Python requirement: ≥3.12
- 9 production dependencies
- 3 development dependencies
- Minimal but functional setup

**Backend Dockerfile**:
- Multi-stage build (builder + runtime)
- Uses astral-sh/uv container for dependency resolution
- Optimized for size with slim Python base
- Environment isolation with virtual environment
- Exposes port 8000

### Frontend Configuration
**package.json**:
- Dev command: `vite` (hot reload)
- Build command: `tsc -b && vite build`
- Test: `vitest` with UI and coverage options
- Linting: ESLint for code quality

**vite.config.ts**:
- React plugin enabled
- Server bound to 0.0.0.0:3003
- Polling enabled for Docker file watch

**vitest.config.ts**:
- Integrated test runner for Vite

---

## 4. ARCHITECTURE PATTERNS

### API Architecture (Backend)

**FastAPI with Modular Routers**:
```
main.py (FastAPI app setup)
├── CORS middleware (localhost:3003)
├── Lifespan context manager (startup/shutdown)
├── import_router.py (CSV import endpoints)
│   ├── POST /api/import/upload (multi-file handling)
│   └── GET /api/import/status (capabilities)
├── Health endpoints
└── Portfolio endpoints (placeholder)
```

**Router Pattern**:
- Prefix-based organization: `/api/import`
- Tags for OpenAPI documentation
- Type hints for all parameters

**CSV Processing Pipeline**:
```
1. File Upload
   ↓
2. CSVDetector.validate_file()
   ├── Check extension (.csv)
   ├── Verify file size (≤10MB)
   └── Detect type
   ↓
3. get_parser(file_type)
   ├── MetalsParser
   ├── StocksParser
   └── CryptoParser
   ↓
4. parser.parse(content)
   ↓
5. Response with summary
   └── [TODO] Store to database
```

### Frontend Architecture

**Component Hierarchy**:
```
App.tsx (main component)
├── State: portfolio, showImport
├── Effects: fetchPortfolio()
└── Children:
    ├── TransactionImport.tsx
    │   ├── File selection
    │   ├── Drag-and-drop
    │   ├── Type detection
    │   └── Upload progress
    └── Portfolio display
        ├── Summary (total value, cash)
        └── Positions table
```

**State Management**:
- React hooks (useState, useEffect) for local state
- Axios for API communication
- Environment variables for API URL config (VITE_API_URL)

**File Type Detection** (Client-side):
```typescript
detectFileType(filename: string) {
  // Metals: "account-statement_*"
  // Stocks: UUID pattern
  // Crypto: "koinly" (case-insensitive)
  // Unknown: else
}
```

### Data Flow

```
User selects/drops CSV files
    ↓
Frontend detects file types locally
    ↓
FormData multipart sent to /api/import/upload
    ↓
Backend validates each file
    ↓
Appropriate parser selected
    ↓
Transactions extracted (not yet stored)
    ↓
JSON response with summary
    ↓
Frontend displays results
    ↓
[TODO] Store to PostgreSQL
    ↓
[TODO] Refresh portfolio view
```

---

## 5. DATABASE SCHEMA (Planned)

Currently defined in PRD.md, not yet implemented:

```sql
transactions
  id, date, type, ticker, quantity, price, currency,
  fee, raw_description, source_file, created_at

positions
  ticker, total_quantity, avg_cost_basis,
  realized_pl, unrealized_pl, last_updated

price_history
  ticker, date, open, close, high, low, volume

portfolio_snapshots
  date, total_value, cash_balance, positions_json
```

**Status**: Schema creation is Story F5.2-001 (Not Started)

---

## 6. API ENDPOINTS STRUCTURE

### Current Endpoints (Implemented)

| Method | Endpoint | Status | Purpose |
|--------|----------|--------|---------|
| GET | `/` | Active | Root health check |
| GET | `/health` | Active | Health status |
| GET | `/api/import/status` | Active | List supported formats |
| POST | `/api/import/upload` | Active | Multi-file upload with detection |
| GET | `/api/portfolio` | Placeholder | Portfolio data (not implemented) |
| POST | `/api/import/revolut` | Placeholder | Legacy endpoint (deprecated) |

### Endpoint Details

**GET /api/import/status**
- Returns supported CSV formats (METALS, STOCKS, CRYPTO)
- Includes filename patterns and descriptions
- Used by frontend for UI hints

**POST /api/import/upload**
- Accepts multiple files
- Validates each independently
- Returns:
  ```json
  {
    "summary": {
      "total_files": 3,
      "successful": 2,
      "failed": 1,
      "total_transactions": 150
    },
    "files": [
      {
        "filename": "...",
        "status": "success|error",
        "file_type": "METALS|STOCKS|CRYPTO",
        "errors": [],
        "transactions_count": 50,
        "message": "..."
      }
    ]
  }
  ```

---

## 7. TESTING SETUP

### Backend Tests

**File**: `/Users/user/dev/portfolio-management/backend/tests/`

**test_csv_parser.py** (21 tests):
- CSV file type detection
- File validation (size, extension, format)
- Parser factory function
- Edge cases (empty filenames, malformed UUIDs, special characters)
- Coverage: CSVDetector class (complete), validation logic

**test_import_api.py** (15 tests):
- Import status endpoint
- Single file uploads (metals, stocks, crypto)
- Multiple file uploads
- Invalid file handling
- Concurrent upload scenarios
- Error handling and edge cases

### Frontend Tests

**File**: `/Users/user/dev/portfolio-management/frontend/src/components/TransactionImport.test.tsx` (17 tests):
- Component rendering
- File selection and drag-and-drop
- Type detection logic
- Upload interactions
- Error scenarios

### Test Coverage Status
- **Backend**: 36 tests passing (CSV parser + API integration)
- **Frontend**: 17 tests passing (Component tests)
- **Coverage Target**: 85% (per TESTING.md requirements)
- **Current Status**: Early-stage (foundation phase)

**Test Execution**:
```bash
# Backend
pytest tests/ -v
pytest tests/ --cov=. --cov-report=html

# Frontend
npm test
npm run test:coverage
```

---

## 8. BUILD AND DEVELOPMENT COMMANDS

### Backend
```bash
# Install dependencies
uv sync

# Run development server
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Run tests
uv run pytest tests/ -v
uv run pytest tests/ --cov

# Add new dependency
uv add <package>
uv add --dev <package>
```

### Frontend
```bash
# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run tests
npm test
npm run test:ui      # with UI
npm run test:coverage

# Linting
npm run lint
```

### Docker
```bash
# Start all services
docker-compose up

# Build images
docker-compose build

# Stop services
docker-compose down

# View logs
docker-compose logs -f [service-name]
```

---

## 9. BUILD PROCESS & ARTIFACTS

### Backend Dockerfile
- **Stage 1**: Builder with uv dependency resolution
- **Stage 2**: Runtime with minimal Python image
- **Output**: Slim image with virtual environment
- **Command**: `uv run uvicorn main:app --host 0.0.0.0 --port 8000`

### Frontend Dockerfile
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3003
CMD ["npm", "run", "dev"]
```

### Development Setup
- Hot reload enabled for both frontend and backend
- Volume mounts prevent node_modules/venv overwriting
- Database and cache initialize on first run

---

## 10. PROJECT PROGRESS & STATUS

### Epic Overview (77 points total, ~9% complete)

| Epic | Status | Points | Progress | Notes |
|------|--------|--------|----------|-------|
| E1: Transaction Import | 🟡 In Progress | 23 | 13% (3/23 pts) | CSV parsing & upload complete |
| E2: Portfolio Calculation | 🔴 Not Started | 26 | 0% | FIFO algorithm needed |
| E3: Live Market Data | 🔴 Not Started | 16 | 0% | Yahoo Finance integration |
| E4: Visualization | 🔴 Not Started | 19 | 0% | Dashboard & charts |
| E5: Infrastructure | 🟡 In Progress | 13 | 50% | Docker setup done, DB schema pending |
| **Total** | **In Progress** | **97** | **~9%** | MVP target: 76 points |

### Completed Stories
- **F1.1-001**: Multi-File Upload Component (3 pts) ✅
- **F5.1-001**: Multi-Service Docker Setup (5 pts) ✅

### In Progress
- **F5.3-001**: Hot Reload Setup (3 pts) 🟡

### Immediate Next Steps
1. F5.2-001: Create Database Tables (5 pts)
2. F5.3-001: Complete Hot Reload Setup (3 pts)
3. F1.1-002: Upload Status Feedback (2 pts)
4. F1.2-001: Parse Metals Transactions (5 pts)

---

## 11. KEY IMPLEMENTATION PATTERNS

### CSV Detection Strategy
```python
class CSVDetector:
    @staticmethod
    def detect_file_type(filename: str) -> FileType:
        # Pattern matching on filename
        if filename.startswith('account-statement_'):
            return FileType.METALS
        if re.match(uuid_pattern, filename, re.IGNORECASE):
            return FileType.STOCKS
        if 'koinly' in filename.lower():
            return FileType.CRYPTO
        return FileType.UNKNOWN
```

### Parser Factory Pattern
```python
def get_parser(file_type: FileType) -> Optional[CSVParser]:
    parsers = {
        FileType.METALS: MetalsParser(),
        FileType.STOCKS: StocksParser(),
        FileType.CRYPTO: CryptoParser()
    }
    return parsers.get(file_type)
```

### Async File Upload Handling
```python
@router.post("/upload")
async def upload_csv_files(files: List[UploadFile] = File(...)):
    for file in files:
        content = await file.read()
        # Validate and process
        transactions = parser.parse(content)
        # TODO: Store to database
```

---

## 12. ENVIRONMENT CONFIGURATION

### Environment Variables

**Backend** (Docker):
```
DATABASE_URL=postgresql://trader:profits123@postgres:5432/portfolio
REDIS_URL=redis://redis:6379
PYTHONUNBUFFERED=1
```

**Frontend** (Vite):
```
VITE_API_URL=http://localhost:8000
```

**Database Credentials** (Development):
- User: `trader`
- Password: `profits123`
- Database: `portfolio`
- Host: `postgres` (in Docker network)

### Port Mapping
- Backend: 8000 → 8000
- Frontend: 3003 → 3003
- PostgreSQL: 5432 → 5432
- Redis: 6379 → 6379

---

## 13. CODE ORGANIZATION PRINCIPLES

### Comment Style
All Python and TypeScript files start with:
```
// ABOUTME: [Purpose of file]
// ABOUTME: [Key responsibility]
```

This makes code search and documentation trivial.

### Code Conventions
- **Python**: Type hints, docstrings, pytest for testing
- **TypeScript**: Strict mode, React hooks, ESLint
- **Styling**: Tailwind CSS utility-first approach
- **Testing**: TDD approach required (85% coverage minimum)

### Module Organization
- **Backend**: Single root directory, routers included via APIRouter
- **Frontend**: Component-based, colocated tests with components
- **No shared code**: Frontend/backend communicate via REST API only

---

## 14. CURRENT GAPS & LIMITATIONS

### Not Yet Implemented
1. **Database Layer**: No SQLAlchemy models or migrations
2. **Parser Implementations**: MetalsParser, StocksParser, CryptoParser are stubs
3. **Portfolio Calculation**: FIFO algorithm, P&L calculations
4. **Live Prices**: Yahoo Finance integration with caching
5. **Dashboard**: Full UI, charts, real-time updates
6. **Authentication**: No user system
7. **Error Recovery**: Limited retry/recovery logic

### Known Issues
- None documented in code (project is early stage)

### TODOs in Code
- `csv_parser.py`: Parser implementations (lines 103, 111, 119)
- `import_router.py`: Store transactions to database (line 64)
- `main.py`: Database initialization (line 21)

---

## 15. DEVELOPMENT WORKFLOW RECOMMENDATIONS

### Day-to-Day Development
1. **Backend changes**: 
   - Write tests first (test_*.py)
   - Implement feature
   - Run `pytest` with coverage
   - Ensure 85%+ coverage

2. **Frontend changes**:
   - Update TypeScript components
   - Add/update tests (.test.tsx)
   - Run `npm test`
   - Check type safety: `tsc --noEmit`

3. **Git workflow**:
   - Commit with conventional commit format
   - Reference story ID (e.g., F1.1-002)
   - Keep commits focused and small

### Testing Checklist
- Unit tests for business logic
- Integration tests for API endpoints
- Component tests for UI
- Coverage reports generated
- All tests pass before committing

---

## 16. PERFORMANCE CONSIDERATIONS

### Current Setup
- **CSV Import**: Should handle 10,000 transactions in <5 seconds
- **Dashboard Load**: Target <2 seconds
- **Price Updates**: <500ms for portfolio refresh
- **Chart Rendering**: <500ms for 1000 data points

### Optimization Opportunities
1. Redis caching for market data
2. Batch imports for large CSVs
3. Lazy loading for charts
4. Index optimization on PostgreSQL
5. Frontend code splitting with Vite

---

## 17. DEPLOYMENT NOTES

### Docker Production Setup
```yaml
# Multi-stage builds already in place
# Security considerations:
# - Remove hardcoded credentials from docker-compose.yml
# - Use environment files (.env not in git)
# - Run containers as non-root user
# - Health checks enabled
```

### Database Persistence
- PostgreSQL data persists via volume `postgres_data`
- Redis ephemeral (can add volume if needed)
- File uploads stored in `/data` and `/uploads`

---

## SUMMARY

The Portfolio Management application is a **well-structured, test-driven learning project** with:

- Clear separation of concerns (backend/frontend)
- Solid foundational architecture using modern tools (FastAPI, React, Docker)
- Comprehensive testing framework (85% coverage requirement)
- Documented roadmap across 5 epics with 21 stories
- CSV detection and upload complete; parsing stub implementations
- Zero database integration yet (next priority)
- Development environment fully containerized

**Next Critical Path**: Database schema → Parser implementations → P&L calculations → Live prices → Dashboard visualization

The codebase follows clean code principles with ABOUTME headers, type hints, and modular architecture. All configuration is environment-driven and containerized.

