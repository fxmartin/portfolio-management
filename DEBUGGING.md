# Debugging Guide - Portfolio Management

This guide covers debugging techniques for the Portfolio Management application, including VS Code setup, Docker debugging, and common troubleshooting scenarios.

## Table of Contents
1. [Quick Start](#quick-start)
2. [VS Code Debugging](#vs-code-debugging)
3. [Backend Debugging](#backend-debugging)
4. [Frontend Debugging](#frontend-debugging)
5. [Database Debugging](#database-debugging)
6. [Common Issues](#common-issues)
7. [Performance Profiling](#performance-profiling)

---

## Quick Start

### Development Environment
```bash
# Start all services in development mode with hot-reload
make dev

# Or with docker-compose directly
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Start with PgAdmin for database management
make dev-tools
```

### Access Services
- **Frontend**: http://localhost:3003
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **PgAdmin**: http://localhost:5050 (when using dev-tools)
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

---

## VS Code Debugging

### Prerequisites
Install recommended VS Code extensions:
- **Python**: `ms-python.python`
- **Pylance**: `ms-python.vscode-pylance`
- **Python Debugger**: `ms-python.debugpy`
- **ESLint**: `dbaeumer.vscode-eslint`
- **Prettier**: `esbenp.prettier-vscode`
- **Docker**: `ms-azuretools.vscode-docker`

### Available Debug Configurations

#### 1. Backend: Attach to Docker
Attach debugger to running backend container.

**Steps**:
1. Start services: `make dev`
2. Set breakpoints in Python code
3. Press F5 or select "Backend: Attach to Docker"
4. Trigger the code path (e.g., API request)

**Port**: 5678 (debugpy default)

#### 2. Backend: Run Tests
Debug backend tests with breakpoints.

**Steps**:
1. Open test file in VS Code
2. Set breakpoints
3. Select "Backend: Run Tests" from debug menu
4. Press F5

**Output**: Integrated terminal with full test logs

#### 3. Frontend: Chrome
Debug React app in Chrome with source maps.

**Steps**:
1. Start services: `make dev`
2. Set breakpoints in TypeScript/React code
3. Select "Frontend: Chrome" from debug menu
4. Press F5 (opens Chrome with debugger attached)

#### 4. Full Stack: Debug All
Debug both frontend and backend simultaneously.

**Steps**:
1. Start services: `make dev`
2. Select "Full Stack: Debug All"
3. Press F5
4. Set breakpoints in both backend and frontend

---

## Backend Debugging

### Enable Debug Mode in Docker

**Method 1: Environment Variable** (Recommended)
```bash
# Edit .env file
DEBUG=true
LOG_LEVEL=debug

# Restart services
docker-compose restart backend
```

**Method 2: Temporary Override**
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Remote Debugging with debugpy

Add to your Python code:
```python
import debugpy

# Wait for debugger to attach
debugpy.listen(("0.0.0.0", 5678))
print("⏳ Waiting for debugger to attach...")
debugpy.wait_for_client()
print("✅ Debugger attached!")
```

Then attach VS Code debugger.

### Logging Best Practices

```python
import logging

logger = logging.getLogger(__name__)

# Different log levels
logger.debug("Detailed diagnostic information")
logger.info("General informational messages")
logger.warning("Warning messages")
logger.error("Error messages")
logger.exception("Exception with full traceback")
```

### Interactive Shell in Container
```bash
# Python REPL with app context
make shell-backend

# Then in container:
python3
>>> from database import get_db
>>> from models import Transaction
>>> # Interactive debugging
```

### Database Query Logging

Enable SQL logging in `database.py`:
```python
engine = create_engine(
    DATABASE_URL,
    echo=True  # Log all SQL queries
)
```

---

## Frontend Debugging

### Browser DevTools

**Chrome DevTools**:
1. Open http://localhost:3003
2. Press F12 or Cmd+Option+I (Mac) / Ctrl+Shift+I (Windows)
3. Source maps enabled automatically (see Vite config)

**React DevTools**:
Install [React Developer Tools](https://react.dev/learn/react-developer-tools)
- Inspect component tree
- View props and state
- Profile component renders

### Console Logging
```typescript
// Development-only logs
if (import.meta.env.DEV) {
  console.log('Debug info:', data);
}

// Structured logging
console.table(arrayData);  // Pretty tables
console.group('API Response');
console.log('Status:', response.status);
console.log('Data:', response.data);
console.groupEnd();
```

### Network Debugging

**Check API calls in DevTools**:
1. Open Network tab
2. Filter by "XHR" or "Fetch"
3. Click request to see headers, payload, response

**Proxy Issues**:
Check `vite.config.ts` proxy settings:
```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://backend:8000',
      changeOrigin: true,
    },
  },
}
```

### Hot Module Replacement (HMR)

HMR should work automatically. If not:
```bash
# Check logs
make logs-frontend

# Rebuild with clean cache
docker-compose down
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

---

## Database Debugging

### Access PostgreSQL Shell
```bash
# Via Makefile
make shell-db

# Or directly
docker-compose exec postgres psql -U trader portfolio
```

### Common SQL Queries
```sql
-- View all transactions
SELECT * FROM transactions ORDER BY transaction_date DESC LIMIT 10;

-- Check positions
SELECT * FROM positions;

-- Transaction counts by type
SELECT transaction_type, COUNT(*)
FROM transactions
GROUP BY transaction_type;

-- Recent price updates
SELECT * FROM price_history
ORDER BY created_at DESC
LIMIT 20;
```

### Database GUI: PgAdmin

Start with dev-tools profile:
```bash
make dev-tools
```

Access PgAdmin:
1. Open http://localhost:5050
2. Login: `admin@portfolio.local` / `admin` (or from .env)
3. Add server:
   - Host: `postgres`
   - Port: `5432`
   - Username: `trader` (from .env)
   - Password: from .env
   - Database: `portfolio`

### View Logs
```bash
# PostgreSQL logs
docker-compose logs postgres

# Follow logs in real-time
docker-compose logs -f postgres
```

---

## Common Issues

### Issue: Backend Won't Start

**Symptoms**: Backend container exits immediately

**Solutions**:
```bash
# Check logs
make logs-backend

# Common causes:
# 1. Database not ready
docker-compose ps  # Check postgres is healthy

# 2. Missing dependencies
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# 3. Port conflict
lsof -i :8000  # Check what's using port 8000
```

### Issue: Frontend Hot Reload Not Working

**Symptoms**: Code changes don't reflect in browser

**Solutions**:
```bash
# 1. Check volume mounts
docker-compose config | grep volumes

# 2. Restart frontend
docker-compose restart frontend

# 3. Clear browser cache
# Chrome: Cmd+Shift+R (Mac) / Ctrl+F5 (Windows)

# 4. Check Vite config
cat frontend/vite.config.ts | grep usePolling
# Should be: usePolling: true
```

### Issue: Database Connection Errors

**Symptoms**: `psycopg2.OperationalError: could not connect to server`

**Solutions**:
```bash
# 1. Check PostgreSQL is running
docker-compose ps postgres

# 2. Check health
docker-compose exec postgres pg_isready -U trader

# 3. Verify connection string
echo $DATABASE_URL

# 4. Check network
docker network ls
docker network inspect portfolio-network
```

### Issue: Redis Connection Errors

**Symptoms**: `redis.exceptions.ConnectionError`

**Solutions**:
```bash
# 1. Check Redis is running
docker-compose ps redis

# 2. Test connection
docker-compose exec redis redis-cli ping
# Should return: PONG

# 3. Check connection string
echo $REDIS_URL
```

### Issue: Tests Failing

**Backend Tests**:
```bash
# Run with verbose output
make test-backend

# Run specific test
docker-compose exec backend uv run pytest tests/test_fifo_calculator.py -v

# Clear pytest cache
docker-compose exec backend rm -rf .pytest_cache
```

**Frontend Tests**:
```bash
# Run tests
make test-frontend

# Run specific test file
docker-compose exec frontend npm test -- HoldingsTable.test.tsx

# Update snapshots
docker-compose exec frontend npm test -- -u
```

---

## Performance Profiling

### Backend Performance

**Profile Python Code**:
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here
calculate_positions()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 slowest
```

**Memory Profiling**:
```bash
# Install memory_profiler
uv add --dev memory-profiler

# Run with memory profiling
docker-compose exec backend python -m memory_profiler script.py
```

### Frontend Performance

**React Profiler**:
1. Install React DevTools
2. Open DevTools → Profiler tab
3. Click Record
4. Interact with app
5. Stop recording
6. Analyze component render times

**Lighthouse**:
1. Open Chrome DevTools
2. Lighthouse tab
3. Generate report
4. Review performance metrics

**Bundle Size Analysis**:
```bash
# Analyze bundle
cd frontend
npm run build
npx vite-bundle-visualizer
```

---

## Additional Resources

### Docker Commands
```bash
# View all logs
make logs

# Rebuild single service
docker-compose up --build backend

# Remove all containers and volumes
make clean-all

# System cleanup
make prune
```

### Helper Scripts
All available in Makefile:
```bash
make help  # Show all commands
```

### Environment Variables
Check `.env.example` for all available configuration options.

### Testing
See `TESTING.md` for comprehensive testing guide.

---

## Getting Help

1. **Check Logs First**: `make logs`
2. **Search Issues**: Check if problem already reported
3. **Documentation**: Review CLAUDE.md and STORIES.md
4. **Clean Restart**: `make dev-clean`

**Still stuck?** Create a GitHub issue with:
- Error message / logs
- Steps to reproduce
- Docker version: `docker --version`
- Docker Compose version: `docker-compose --version`
