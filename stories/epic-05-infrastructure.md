# Epic 5: Infrastructure & DevOps

## Epic Overview
**Epic ID**: EPIC-05
**Epic Name**: Infrastructure & DevOps
**Epic Description**: Docker containerization and development environment setup
**Business Value**: Single command deployment, consistent development environment
**User Impact**: Easy setup and deployment for learning and development
**Success Metrics**: `docker-compose up` starts all services, hot-reload works for development
**Status**: 🟢 Partially Complete

## Features in this Epic
- Feature 5.1: Docker Compose Configuration
- Feature 5.2: Database Schema Setup
- Feature 5.3: Development Environment

## Progress Tracking
| Feature | Stories | Points | Status | Progress |
|---------|---------|--------|--------|----------|
| F5.1: Docker Compose | 1 | 5 | 🟢 Complete | 100% |
| F5.2: Database Schema | 1 | 5 | 🟢 Complete | 100% |
| F5.3: Dev Environment | 1 | 3 | 🟡 In Progress | 50% |
| **Total** | **3** | **13** | **In Progress** | **85%** (11/13 pts) |

---

## Feature 5.1: Docker Compose Configuration
**Feature Description**: Multi-service Docker setup for all application components
**User Value**: Single command to start entire development environment
**Priority**: High
**Complexity**: 5 story points

### Story F5.1-001: Multi-Service Docker Setup
**Status**: 🟢 Complete
**User Story**: As FX, I want to start all services with one command so that development setup is simple

**Acceptance Criteria**:
- **Given** the docker-compose.yml file
- **When** running `docker-compose up`
- **Then** PostgreSQL starts and is accessible on port 5432
- **And** Redis starts and is accessible on port 6379
- **And** Backend API starts on port 8000
- **And** Frontend starts on port 3003
- **And** all services can communicate
- **And** health checks ensure services are ready
- **And** volumes persist data between restarts

**Technical Requirements**:
- Docker Compose v3.8+
- Service dependencies
- Health checks
- Volume mounts
- Environment variables
- Network configuration

**Current Implementation**:
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: portfolio-postgres
    environment:
      POSTGRES_DB: portfolio
      POSTGRES_USER: trader
      POSTGRES_PASSWORD: profits123
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U trader -d portfolio"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: portfolio-redis
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: portfolio-backend
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://trader:profits123@postgres:5432/portfolio
      REDIS_URL: redis://redis:6379
      PYTHONUNBUFFERED: 1
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - ./data:/data
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: portfolio-frontend
    depends_on:
      - backend
    ports:
      - "3003:3003"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      VITE_API_URL: http://localhost:8000
    command: npm run dev

volumes:
  postgres_data:

networks:
  default:
    name: portfolio-network
```

**Definition of Done**:
- [x] Docker Compose file configured
- [x] Service dependencies defined
- [x] Health checks implemented
- [x] Volume mounts for development
- [x] Environment variables configured
- [x] Network configuration
- [x] All services start successfully
- [x] Services can communicate
- [x] README with Docker instructions

**Story Points**: 5
**Priority**: Must Have
**Dependencies**: None
**Risk Level**: Medium
**Assigned To**: Completed

---

## Feature 5.2: Database Schema Setup
**Feature Description**: Automatic database schema creation and migrations
**User Value**: No manual SQL setup required, database ready immediately
**Priority**: High
**Complexity**: 5 story points

### Story F5.2-001: Create Database Tables
**Status**: ✅ Complete (2025-10-21)
**User Story**: As FX, I want the database schema automatically created so that I don't need to run SQL manually

**Acceptance Criteria**:
- **Given** the application starts for the first time
- **When** connecting to database
- **Then** transactions table is created if not exists
- **And** positions table is created if not exists
- **And** price_history table is created if not exists
- **And** portfolio_snapshots table is created if not exists
- **And** appropriate indexes are created
- **And** foreign key constraints are enforced
- **And** migrations run automatically on startup

**Technical Requirements**:
- SQLAlchemy ORM models
- Alembic for migrations
- Auto-migration on startup
- Index optimization
- Constraint definitions

**Implementation Notes**:
- Created comprehensive SQLAlchemy models with proper enums for AssetType and TransactionType
- Implemented Transaction, Position, PriceHistory, and PortfolioSnapshot tables
- Set up Alembic with automatic migration generation
- Added async database connection manager with pooling
- Integrated database initialization into FastAPI startup
- Created proper indexes for performance (symbol, date, asset_type)
- Added unique constraints to prevent duplicate transactions
- JSON fields for flexible data storage (cost_lots, positions_snapshot)
- 9 database tests passing with 100% model coverage

**Database Schema Design**:
```python
# models.py
from sqlalchemy import Column, Integer, String, DateTime, Decimal, ForeignKey, Index, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True)
    transaction_date = Column(DateTime, nullable=False, index=True)
    transaction_type = Column(String(20), nullable=False, index=True)
    ticker = Column(String(10), index=True)
    quantity = Column(Decimal(18, 8))
    price = Column(Decimal(18, 8))
    total_amount = Column(Decimal(18, 8))
    currency = Column(String(3))
    fee = Column(Decimal(18, 8), default=0)
    raw_description = Column(String(500))
    source_file = Column(String(255))
    import_timestamp = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint('transaction_date', 'ticker', 'quantity', 'transaction_type',
                         name='uix_transaction_unique'),
        Index('idx_ticker_date', 'ticker', 'transaction_date'),
    )

class Position(Base):
    __tablename__ = 'positions'

    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), unique=True, nullable=False)
    quantity = Column(Decimal(18, 8), nullable=False)
    avg_cost_basis = Column(Decimal(18, 8))
    total_cost = Column(Decimal(18, 8))
    realized_pl = Column(Decimal(18, 8), default=0)
    unrealized_pl = Column(Decimal(18, 8), default=0)
    last_price = Column(Decimal(18, 8))
    last_updated = Column(DateTime, default=func.now())

    # Relationships
    lots = relationship("Lot", back_populates="position")

class Lot(Base):
    __tablename__ = 'lots'

    id = Column(Integer, primary_key=True)
    position_id = Column(Integer, ForeignKey('positions.id'))
    purchase_date = Column(DateTime, nullable=False)
    quantity = Column(Decimal(18, 8), nullable=False)
    remaining_quantity = Column(Decimal(18, 8), nullable=False)
    purchase_price = Column(Decimal(18, 8), nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    position = relationship("Position", back_populates="lots")

class PriceHistory(Base):
    __tablename__ = 'price_history'

    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    open_price = Column(Decimal(18, 8))
    high_price = Column(Decimal(18, 8))
    low_price = Column(Decimal(18, 8))
    close_price = Column(Decimal(18, 8))
    volume = Column(Integer)
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint('ticker', 'date', name='uix_price_history'),
        Index('idx_price_ticker_date', 'ticker', 'date'),
    )

class PortfolioSnapshot(Base):
    __tablename__ = 'portfolio_snapshots'

    id = Column(Integer, primary_key=True)
    snapshot_date = Column(DateTime, nullable=False, unique=True)
    total_value = Column(Decimal(18, 8), nullable=False)
    cash_balance = Column(Decimal(18, 8), default=0)
    positions_json = Column(String)  # JSON blob of positions
    created_at = Column(DateTime, default=func.now())
```

**Migration Script**:
```python
# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alembic import command
from alembic.config import Config
import os

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database with tables and run migrations"""
    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Run Alembic migrations
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

    # Create initial indexes if needed
    with engine.connect() as conn:
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_import
            ON transactions(source_file, import_timestamp);
        """)

def get_db():
    """Dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Definition of Done**:
- [x] SQLAlchemy models defined for all tables
- [x] Alembic migrations configured
- [x] Auto-migration on startup implemented
- [x] All indexes created for performance
- [x] Foreign key constraints working
- [x] Unique constraints preventing duplicates
- [x] Database initialization script
- [x] Unit tests for models
- [x] Integration tests with PostgreSQL
- [x] Documentation of schema

**Story Points**: 5
**Priority**: Must Have
**Dependencies**: F5.1-001 (Docker Setup)
**Risk Level**: Medium
**Assigned To**: Unassigned

---

## Feature 5.3: Development Environment
**Feature Description**: Hot reload and development tools setup
**User Value**: Efficient development with instant feedback on code changes
**Priority**: High
**Complexity**: 3 story points

### Story F5.3-001: Hot Reload Setup
**Status**: 🟡 In Progress
**User Story**: As FX, I want code changes to reload automatically so that development is efficient

**Acceptance Criteria**:
- **Given** the development environment is running
- **When** I modify Python or React code
- **Then** backend reloads automatically within 2 seconds
- **And** frontend reloads with hot module replacement (HMR)
- **And** state is preserved when possible in frontend
- **And** error messages are clear and actionable
- **And** source maps work for debugging

**Technical Requirements**:
- FastAPI with --reload flag
- Vite HMR configuration
- Docker volume mounts
- Error overlay in frontend
- Source maps generation

**Current Backend Setup**:
```python
# main.py with auto-reload
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload
        reload_dirs=["./"],  # Watch directories
        log_level="debug" if DEBUG else "info"
    )
```

**Current Frontend Setup**:
```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3003,
    watch: {
      usePolling: true,  // For Docker
    },
    hmr: {
      overlay: true,  // Show errors in browser
    },
  },
  build: {
    sourcemap: true,  // Enable source maps
  },
});
```

**Development Tools Configuration**:
```yaml
# docker-compose.dev.yml (override for development)
version: '3.8'

services:
  backend:
    environment:
      - DEBUG=true
      - LOG_LEVEL=debug
    volumes:
      - ./backend:/app:cached  # Cached for performance
    command: python main.py  # Uses reload=True

  frontend:
    environment:
      - NODE_ENV=development
    volumes:
      - ./frontend/src:/app/src:cached
      - ./frontend/public:/app/public:cached
    stdin_open: true  # For React error overlay
    tty: true

  # Development-only services
  pgadmin:
    image: dpage/pgadmin4
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@example.com
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "5050:80"
    depends_on:
      - postgres
```

**Developer Scripts**:
```json
// package.json scripts
{
  "scripts": {
    "dev": "docker-compose up",
    "dev:rebuild": "docker-compose up --build",
    "dev:clean": "docker-compose down -v && docker-compose up",
    "logs": "docker-compose logs -f",
    "shell:backend": "docker-compose exec backend bash",
    "shell:db": "docker-compose exec postgres psql -U trader portfolio",
    "test": "docker-compose run backend pytest",
    "format": "docker-compose run backend black . && npm run format:frontend",
    "format:frontend": "prettier --write 'src/**/*.{ts,tsx}'"
  }
}
```

**Definition of Done**:
- [x] FastAPI reload configured
- [x] Vite HMR configured
- [x] Docker volumes for code mounting
- [ ] Error overlay in frontend
- [ ] Development vs production configs
- [ ] Developer helper scripts
- [ ] Debugging documentation
- [ ] VS Code launch.json for debugging
- [ ] Pre-commit hooks setup

**Story Points**: 3
**Priority**: Must Have
**Dependencies**: F5.1-001 (Docker Setup)
**Risk Level**: Low
**Assigned To**: In Progress

---

## Additional Infrastructure Considerations

### Monitoring & Logging
```python
# Structured logging setup
import structlog

logger = structlog.get_logger()

# Log aggregation with Docker
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Performance Monitoring
- APM integration (optional)
- Database query logging
- API response time tracking
- Resource usage monitoring

### Security Considerations
- Environment variable management
- Secret rotation
- Database connection pooling
- CORS configuration
- Rate limiting

### Backup Strategy
```bash
# Database backup script
docker-compose exec postgres pg_dump -U trader portfolio > backup_$(date +%Y%m%d).sql

# Restore from backup
docker-compose exec -T postgres psql -U trader portfolio < backup.sql
```

---

## Dependencies
- **External**: Docker, Docker Compose, PostgreSQL, Redis
- **Internal**: Must complete before other epics can run
- **Libraries**: SQLAlchemy, Alembic, uvicorn

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|---------|------------|
| Docker compatibility issues | Can't run locally | Multiple OS testing, clear requirements |
| Database migrations fail | Data corruption | Backup before migration, rollback plan |
| Hot reload not working | Slow development | Fallback to manual restart, debug guides |
| Port conflicts | Services won't start | Configurable ports, port check script |

## Testing Strategy

**⚠️ MANDATORY TESTING REQUIREMENT**:
- **Minimum Coverage Threshold**: 85% code coverage for all modules
- **No story is complete without passing tests meeting this threshold**

1. **Infrastructure Tests**: Docker Compose validation
2. **Database Tests**: Schema creation, migrations
3. **Integration Tests** (Required): Service communication
4. **Performance Tests**: Startup time, reload speed
5. **Developer Experience**: New developer onboarding

## Performance Requirements
- Docker Compose startup: <30 seconds
- Hot reload trigger: <2 seconds
- Database migration: <5 seconds
- Full environment teardown: <10 seconds

## Definition of Done for Epic
- [x] All services start with `docker-compose up`
- [x] Database schema automatically created
- [x] Hot reload working for backend and frontend
- [x] Health checks ensure service readiness
- [ ] Development tools and scripts provided
- [ ] Environment variables properly configured
- [x] Volume persistence working
- [ ] Documentation for setup and troubleshooting
- [ ] Works on Mac, Linux, and Windows (WSL2)
- [x] Unit test coverage ≥85% for database models and utilities (mandatory threshold)