# Command Reference

Complete guide to all available commands in the Portfolio Management application.

## Quick Command Index

```bash
make help              # Show all available commands
make dev               # Start development environment
make test              # Run all tests
make logs              # View all service logs
make clean             # Stop all services
```

---

## Makefile Commands

All commands are run from the project root directory.

### Development Commands

#### `make dev`
Start all services in development mode with hot-reload.

**What it does:**
- Starts PostgreSQL, Redis, Backend, Frontend
- Enables hot-reload (code changes auto-refresh)
- Mounts source directories as volumes
- Opens ports for local access

**Services started:**
- Backend: http://localhost:8000
- Frontend: http://localhost:3003
- PostgreSQL: localhost:5432
- Redis: localhost:6379

**Example:**
```bash
make dev
# Wait for services to start (2-3 minutes first time)
# Access frontend at http://localhost:3003
```

---

#### `make dev-tools`
Start all services plus development tools (pgAdmin).

**Includes everything in `make dev` plus:**
- pgAdmin: http://localhost:5050 (PostgreSQL admin UI)

**Example:**
```bash
make dev-tools
# Login to pgAdmin:
# Email: admin@admin.com
# Password: admin
```

---

#### `make dev-rebuild`
Rebuild Docker images and start services.

**Use when:**
- Dependencies changed (package.json, pyproject.toml)
- Dockerfile modified
- Fresh build needed

**Example:**
```bash
# After updating requirements
make dev-rebuild
```

---

#### `make dev-clean`
Clean volumes and start fresh.

**⚠️ WARNING:** Deletes all data (database, cache)

**What it does:**
- Stops all services
- Removes Docker volumes
- Rebuilds images
- Starts fresh services

**Example:**
```bash
make dev-clean
# All data will be lost - confirm: yes
```

---

### Production Commands

#### `make prod`
Start all services in production mode.

**Differences from dev:**
- No hot-reload
- Optimized builds
- Production-ready configuration
- Runs in background (detached)

**Example:**
```bash
make prod
# Services run in background
# View logs with: make logs
```

---

### Logs & Monitoring

#### `make logs`
Follow logs from all services.

**Example:**
```bash
make logs
# Press Ctrl+C to stop following
```

**Output:**
```
backend_1   | INFO: Uvicorn running on http://0.0.0.0:8000
frontend_1  | VITE ready in 250ms
postgres_1  | database system is ready to accept connections
```

---

#### `make logs-backend`
Follow backend logs only.

**Example:**
```bash
make logs-backend
# See Python/FastAPI output
```

---

#### `make logs-frontend`
Follow frontend logs only.

**Example:**
```bash
make logs-frontend
# See Vite/React output
```

---

### Shell Access

#### `make shell-backend`
Open bash shell in backend container.

**Use for:**
- Run Python commands
- Install packages (uv add)
- Debug backend issues
- Run database migrations

**Example:**
```bash
make shell-backend
# Now in backend container
uv run python
>>> from database import engine
>>> print(engine)
```

---

#### `make shell-db`
Open PostgreSQL shell.

**Use for:**
- Run SQL queries
- Inspect database
- Manual data fixes

**Example:**
```bash
make shell-db
# Now in PostgreSQL shell
portfolio=# \dt  -- List tables
portfolio=# SELECT COUNT(*) FROM transactions;
```

---

#### `make shell-frontend`
Open sh shell in frontend container.

**Use for:**
- Run npm commands
- Debug frontend build
- Install packages

**Example:**
```bash
make shell-frontend
# Now in frontend container
npm run build
```

---

### Testing Commands

#### `make test`
Run all tests (backend + frontend).

**What it runs:**
- Backend: pytest with coverage
- Frontend: vitest

**Example:**
```bash
make test
# Runs 676 backend tests + 372 frontend tests
```

---

#### `make test-backend`
Run backend tests with coverage report.

**Example:**
```bash
make test-backend
# Output:
# ========== 676 passed in 45.2s ==========
# Coverage: 92%
```

**Coverage report:**
- Terminal output (summary)
- HTML report: `backend/htmlcov/index.html`

---

#### `make test-frontend`
Run frontend tests.

**Example:**
```bash
make test-frontend
# Runs Vitest tests
```

---

### Code Quality Commands

#### `make format`
Format all code (backend + frontend).

**What it does:**
- Backend: Black + isort (Python)
- Frontend: Prettier (TypeScript/JSX)

**Example:**
```bash
make format
# All files reformatted
```

---

#### `make format-backend`
Format backend Python code.

**Tools:**
- Black: Code formatter
- isort: Import sorter

**Example:**
```bash
make format-backend
# reformatted backend/main.py
# reformatted backend/csv_parser.py
```

---

#### `make format-frontend`
Format frontend TypeScript code.

**Tool:** Prettier

**Example:**
```bash
make format-frontend
# src/App.tsx 150ms
# src/components/HoldingsTable.tsx 85ms
```

---

#### `make lint`
Run linters on all code.

**Tools:**
- Backend: Ruff (Python linter)
- Frontend: ESLint (TypeScript linter)

**Example:**
```bash
make lint
# Found 0 errors
```

---

### Database Commands

#### `make backup`
Backup PostgreSQL database.

**Output:** `./backups/backup_YYYYMMDD_HHMMSS.sql`

**Example:**
```bash
make backup
# Creating backup...
# Backup created in ./backups/backup_20251106_183000.sql
```

**Backup includes:**
- All tables
- All data
- Schema structure

---

#### `make restore FILE=<file>`
Restore database from backup.

**⚠️ WARNING:** Overwrites current data

**Example:**
```bash
make restore FILE=./backups/backup_20251106_183000.sql
# Restoring from ./backups/backup_20251106_183000.sql...
# Database restored!
```

---

#### `make db-reset`
Reset database (delete all data).

**⚠️ WARNING:** Irreversible!

**Example:**
```bash
make db-reset
# WARNING: This will delete ALL data!
# Are you sure? (yes/no): yes
# Resetting database...
# Done!
```

---

### Cleanup Commands

#### `make clean`
Stop all services (keep data).

**Example:**
```bash
make clean
# Stopping containers...
# Done
```

---

#### `make clean-all`
Stop all services and remove volumes.

**⚠️ WARNING:** Deletes all data (database, cache, backups)

**Example:**
```bash
make clean-all
# Stopping containers...
# Removing volumes...
# Removing backups...
# Done
```

---

#### `make prune`
Remove unused Docker resources.

**What it removes:**
- Stopped containers
- Unused images
- Unused volumes
- Build cache

**Example:**
```bash
make prune
# Removed: 2GB disk space
```

---

### Installation Commands

#### `make install`
Install dependencies (backend + frontend).

**What it does:**
- Backend: `uv sync`
- Frontend: `npm install`

**Use when:**
- First time setup
- After pulling code changes
- Dependencies out of sync

**Example:**
```bash
make install
# Installing backend dependencies...
# Installing frontend dependencies...
# Done
```

---

#### `make install-backend`
Install backend Python dependencies.

**Example:**
```bash
make install-backend
# uv sync
# Resolved 45 packages in 1.2s
```

---

#### `make install-frontend`
Install frontend Node dependencies.

**Example:**
```bash
make install-frontend
# npm install
# added 1250 packages in 15s
```

---

## Docker Commands

Direct Docker commands for advanced usage.

### Container Management

```bash
# List running containers
docker-compose ps

# Start specific service
docker-compose up backend

# Stop specific service
docker-compose stop backend

# Restart service
docker-compose restart backend

# Remove stopped containers
docker-compose rm
```

---

### Logs & Debugging

```bash
# Follow logs for specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend

# Logs since timestamp
docker-compose logs --since 2024-11-06T18:00:00 backend
```

---

### Exec Commands

```bash
# Run command in container
docker-compose exec backend uv run python -c "print('Hello')"

# Run as specific user
docker-compose exec -u root backend bash

# Run with environment variable
docker-compose exec -e DEBUG=1 backend pytest
```

---

### Volume Management

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect portfolio-management_postgres_data

# Remove specific volume
docker volume rm portfolio-management_postgres_data

# Remove all unused volumes
docker volume prune
```

---

## Backend-Specific Commands

Commands to run inside backend container (`make shell-backend`).

### Package Management

```bash
# Add package
uv add requests

# Add dev dependency
uv add --dev pytest-cov

# Remove package
uv remove requests

# Update all packages
uv sync --upgrade

# Lock dependencies
uv lock
```

---

### Python Scripts

```bash
# Run Python REPL
uv run python

# Run specific script
uv run python scripts/seed_data.py

# Run with environment variable
uv run -e DEBUG=1 python main.py
```

---

### Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_csv_parser.py -v

# Run with coverage
uv run pytest tests/ --cov --cov-report=html

# Run specific test
uv run pytest tests/test_csv_parser.py::test_detect_metals_file -v
```

---

### Database Migrations (if using Alembic)

```bash
# Create migration
uv run alembic revision -m "Add new column"

# Run migrations
uv run alembic upgrade head

# Rollback migration
uv run alembic downgrade -1

# Show current version
uv run alembic current
```

---

## Frontend-Specific Commands

Commands to run inside frontend container (`make shell-frontend`).

### Package Management

```bash
# Install package
npm install axios

# Install dev dependency
npm install --save-dev @types/react

# Remove package
npm uninstall axios

# Update packages
npm update
```

---

### Development

```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type checking
npm run type-check
```

---

### Testing

```bash
# Run tests
npm test

# Run with UI
npm run test:ui

# Run with coverage
npm run test:coverage

# Run specific test file
npm test -- HoldingsTable.test.tsx
```

---

### Linting

```bash
# Run linter
npm run lint

# Fix linting errors
npm run lint:fix
```

---

## Database Commands

Commands to run in PostgreSQL shell (`make shell-db`).

### Table Inspection

```sql
-- List all tables
\dt

-- Describe table structure
\d transactions

-- List indexes
\di

-- List views
\dv
```

---

### Queries

```sql
-- Count transactions
SELECT COUNT(*) FROM transactions;

-- Show recent transactions
SELECT * FROM transactions ORDER BY transaction_date DESC LIMIT 10;

-- Show positions
SELECT symbol, quantity, avg_cost_basis, current_price
FROM positions
WHERE quantity > 0;

-- Total portfolio value
SELECT SUM(current_value) FROM positions;
```

---

### Maintenance

```sql
-- Vacuum database
VACUUM ANALYZE;

-- Check table sizes
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Kill slow queries
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'active' AND query_start < NOW() - INTERVAL '5 minutes';
```

---

## Git Workflow Commands

```bash
# Check status
git status

# Create feature branch
git checkout -b feature/my-feature

# Stage changes
git add .

# Commit (conventional commits)
git commit -m "feat: add new feature"
git commit -m "fix: resolve bug"
git commit -m "docs: update README"

# Push branch
git push -u origin feature/my-feature

# Pull latest
git pull origin main

# Merge main into feature
git checkout feature/my-feature
git merge main
```

---

## Troubleshooting Commands

### Check Service Health

```bash
# Backend health
curl http://localhost:8000/health

# Frontend health
curl http://localhost:3003

# Database health
make shell-db
# \conninfo
```

---

### Debug Container Issues

```bash
# Check container status
docker-compose ps

# View container resource usage
docker stats

# Inspect container
docker inspect portfolio-management-backend-1

# View container logs
docker logs portfolio-management-backend-1
```

---

### Reset Everything

```bash
# Nuclear option - complete reset
make clean-all
docker system prune -a --volumes
make dev
```

---

## Quick Reference

### Daily Development Workflow

```bash
# Start
make dev

# Make changes (hot-reload auto-refreshes)

# Test
make test

# Format code
make format

# Stop
make clean
```

---

### Before Committing

```bash
# Test everything
make test

# Format code
make format

# Lint code
make lint

# Check git status
git status

# Commit
git add .
git commit -m "feat: description"
```

---

### Debugging Workflow

```bash
# View logs
make logs

# Shell into backend
make shell-backend

# Check database
make shell-db

# Reset if needed
make dev-clean
```

---

**Need help?** Run `make help` for command list or see [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
