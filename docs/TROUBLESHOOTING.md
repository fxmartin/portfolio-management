# Troubleshooting Guide

Common problems and solutions for the Portfolio Management application.

## Quick Diagnostics

**Start here:** Run these commands to check system health.

```bash
# Check all services
docker-compose ps

# Check backend health
curl http://localhost:8000/health

# Check frontend
curl http://localhost:3003

# View recent logs
make logs --tail=50
```

---

## Table of Contents

1. [Installation Problems](#installation-problems)
2. [Service Startup Issues](#service-startup-issues)
3. [Database Problems](#database-problems)
4. [Import Errors](#import-errors)
5. [Price Data Issues](#price-data-issues)
6. [Performance Problems](#performance-problems)
7. [API Errors](#api-errors)
8. [Frontend Issues](#frontend-issues)

---

## Installation Problems

### Docker not installed

**Symptoms:**
```bash
make dev
# command not found: docker
```

**Solution:**
1. Install Docker Desktop: https://docs.docker.com/get-docker/
2. Start Docker Desktop
3. Verify: `docker --version`

---

### Docker Compose not found

**Symptoms:**
```bash
make dev
# command not found: docker-compose
```

**Solution:**
```bash
# Docker Compose is included in Docker Desktop
# Or install standalone:
# macOS:
brew install docker-compose

# Linux:
sudo apt-get install docker-compose

# Verify:
docker-compose --version
```

---

### Permission denied (Docker)

**Symptoms:**
```bash
make dev
# permission denied while trying to connect to the Docker daemon socket
```

**Solution:**
```bash
# Add user to docker group (Linux)
sudo usermod -aG docker $USER
newgrp docker

# Or run with sudo (not recommended)
sudo make dev
```

---

## Service Startup Issues

### Port already in use

**Symptoms:**
```
Error: bind: address already in use
Port 8000 is already allocated
```

**Solution 1: Stop conflicting service**
```bash
# Find what's using the port
lsof -i :8000

# Kill the process
kill -9 <PID>
```

**Solution 2: Change port**
Edit `docker-compose.yml`:
```yaml
backend:
  ports:
    - "9000:8000"  # Use port 9000 instead
```

---

### Services won't start

**Symptoms:**
```bash
make dev
# Exited with code 1
```

**Diagnostic steps:**
```bash
# 1. View logs
make logs

# 2. Check specific service
docker-compose logs backend

# 3. Try starting individually
docker-compose up backend
```

**Common causes:**
- Missing `.env` file → Copy from `.env.example`
- Wrong database password → Check `DATABASE_URL` matches `POSTGRES_PASSWORD`
- Port conflicts → Change ports in docker-compose.yml

---

### Container keeps restarting

**Symptoms:**
```bash
docker-compose ps
# STATUS: Restarting (1) 5 seconds ago
```

**Solution:**
```bash
# View crash logs
docker-compose logs backend --tail=100

# Common causes:
# 1. Database not ready
#    Wait 30 seconds and try again

# 2. Missing dependency
make dev-rebuild

# 3. Corrupted volume
make clean-all
make dev
```

---

## Database Problems

### Connection refused

**Symptoms:**
```
sqlalchemy.exc.OperationalError: could not connect to server
Connection refused (localhost:5432)
```

**Solution:**
```bash
# 1. Check PostgreSQL is running
docker-compose ps postgres
# Should show: Up

# 2. Check DATABASE_URL in .env
DATABASE_URL=postgresql://trader:password@postgres:5432/portfolio
# NOT localhost, use 'postgres' for Docker internal network

# 3. Restart database
docker-compose restart postgres
```

---

### Password authentication failed

**Symptoms:**
```
FATAL: password authentication failed for user "trader"
```

**Solution:**
```bash
# 1. Check passwords match in .env
POSTGRES_PASSWORD=your_password
DATABASE_URL=postgresql://trader:your_password@postgres:5432/portfolio
#                                ^^^^^^^^^^^^^ must match

# 2. Reset database
make clean-all
make dev
```

---

### Database locked / timeout

**Symptoms:**
```
database is locked
```

**Solution:**
```bash
# 1. Check for long-running queries
make shell-db

SELECT pid, now() - query_start as duration, query
FROM pg_stat_activity
WHERE state = 'active' AND query_start < NOW() - INTERVAL '1 minute';

# 2. Kill slow queries
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid = <PID>;

# 3. Restart database
docker-compose restart postgres
```

---

### Out of disk space

**Symptoms:**
```
No space left on device
```

**Solution:**
```bash
# 1. Check disk usage
df -h

# 2. Clean Docker resources
make prune
docker system prune -a --volumes

# 3. Remove old backups
rm -rf ./backups/*

# 4. Clear logs
truncate -s 0 /var/log/syslog
```

---

## Import Errors

### File not detected (Unknown type)

**Symptoms:**
```json
{
  "status": "error",
  "file_type": "UNKNOWN",
  "errors": ["Unknown CSV format"]
}
```

**Solution:**
Rename file to match expected pattern:

```bash
# Metals:
mv my_export.csv account-statement_2024-11-01.csv

# Stocks:
mv stocks.csv C3E4F5A6-7B8C-9D0E-1F2A-3B4C5D6E7F8G.csv

# Crypto:
mv crypto.csv portfolio_koinly_export.csv
```

---

### Missing required columns

**Symptoms:**
```json
{
  "errors": ["Invalid CSV format: missing required headers: {'Date', 'Ticker'}"]
}
```

**Solution:**
1. Check column names match exactly (case-sensitive)
2. Re-export from source (Revolut/Koinly)
3. Don't modify CSV in Excel (use text editor)
4. Remove BOM if present:
```bash
sed '1s/^\xEF\xBB\xBF//' input.csv > output.csv
```

---

### Invalid date format

**Symptoms:**
```json
{
  "errors": ["time data '01-11-2024' does not match format '%Y-%m-%d'"]
}
```

**Solution:**
- Expected format: `YYYY-MM-DD` or `YYYY-MM-DD HH:MM:SS`
- Don't modify dates manually
- Re-export from source
- Check locale settings

---

### File too large

**Symptoms:**
```json
{
  "errors": ["File size exceeds 10MB limit (size: 15.25MB)"]
}
```

**Solution:**
- Export smaller date ranges
- Split file into chunks:
```bash
# Split into 5MB chunks
split -b 5m large_file.csv chunk_
```

---

### Duplicate transactions

**Symptoms:**
```json
{
  "skipped_count": 50,
  "message": "skipped 50 duplicates"
}
```

**Solution:**

**Option 1: Skip duplicates (default)**
```bash
# Duplicates are automatically skipped
# No action needed
```

**Option 2: Update existing**
```bash
curl -X POST http://localhost:8000/api/import/upload \
  -F "files=@file.csv" \
  -F "duplicate_strategy=update"
```

**Option 3: Force import**
```bash
curl -X POST http://localhost:8000/api/import/upload \
  -F "files=@file.csv" \
  -F "duplicate_strategy=force"
```

---

## Price Data Issues

### Prices not updating

**Symptoms:**
- Dashboard shows old prices
- "Last updated" timestamp is old

**Solution:**
```bash
# 1. Manual refresh
curl -X POST http://localhost:8000/api/portfolio/refresh-prices

# 2. Check market data providers
curl http://localhost:8000/api/monitoring/market-data

# 3. Check logs for errors
make logs-backend | grep "price"

# 4. Restart backend
docker-compose restart backend
```

---

### Rate limit exceeded

**Symptoms:**
```
Rate limit exceeded for Alpha Vantage (5 calls/minute)
```

**Solution:**
1. **Wait** - Quota resets automatically
2. **Add Twelve Data key** - Higher limits
3. **Increase cache TTL** - Reduce API calls
4. **Check monitoring:**
```bash
curl http://localhost:8000/api/monitoring/market-data
```

---

### Symbol not found

**Symptoms:**
```
Failed to fetch price for INVALID: Symbol not found
```

**Solution:**
1. **Check symbol spelling** - Use correct ticker
2. **European ETFs** - Add exchange suffix:
   - AMEM → AMEM.BE (Brussels)
   - MWOQ → MWOQ.BE (Brussels)
3. **Check ETF_MAPPINGS** in `yahoo_finance_service.py`

---

### USD to EUR conversion error

**Symptoms:**
- Portfolio value incorrect for US stocks
- P&L calculations off by ~8-10%

**Solution:**
```bash
# 1. Check exchange rate cache
curl http://localhost:8000/api/portfolio/summary | jq '.total_value'

# 2. Force price refresh (fetches new rate)
curl -X POST http://localhost:8000/api/portfolio/refresh-prices

# 3. Check logs
make logs-backend | grep "EURUSD"
```

---

## Performance Problems

### Slow dashboard loading

**Symptoms:**
- Dashboard takes >5 seconds to load
- Price refresh times out

**Diagnostic:**
```bash
# Check response times
time curl http://localhost:8000/api/portfolio/summary

# Check cache hit rate
curl http://localhost:8000/api/monitoring/market-data | jq '.yahoo_finance.cache_hit_rate'
```

**Solutions:**

**1. Increase cache TTL:**
- Settings → System Performance
- Increase "Historical Data TTL" to 3600s (1 hour)

**2. Check Redis:**
```bash
docker-compose exec redis redis-cli ping
# Should return: PONG

# Check memory usage
docker-compose exec redis redis-cli info memory
```

**3. Reduce positions:**
- Large portfolios (50+ positions) are slower
- Consider archiving closed positions

---

### High memory usage

**Symptoms:**
```
docker stats
# Shows >90% memory usage
```

**Solution:**
```bash
# 1. Increase Docker memory
# Docker Desktop → Settings → Resources → Memory: 4GB+

# 2. Restart containers
docker-compose restart

# 3. Check for memory leaks
make logs-backend | grep "MemoryError"

# 4. Prune unused resources
make prune
```

---

### Slow CSV import

**Symptoms:**
- Import takes >1 minute for small file
- Progress bar stuck

**Solution:**
```bash
# 1. Check database indexes
make shell-db
SELECT tablename, indexname FROM pg_indexes WHERE schemaname = 'public';

# 2. Vacuum database
VACUUM ANALYZE transactions;

# 3. Check concurrent imports
# Only import one file at a time

# 4. Restart backend
docker-compose restart backend
```

---

## API Errors

### 500 Internal Server Error

**Symptoms:**
```json
{
  "detail": "Internal server error",
  "status_code": 500
}
```

**Diagnostic:**
```bash
# View backend logs
make logs-backend

# Look for Python tracebacks
make logs-backend | grep "Traceback"
```

**Common causes:**
- Database connection lost
- Missing API key
- Invalid data format
- Bug in code

---

### 404 Not Found

**Symptoms:**
```json
{
  "detail": "Position not found for symbol: INVALID",
  "status_code": 404
}
```

**Solution:**
- Check symbol spelling
- Verify position exists in portfolio
- Check transactions imported correctly

---

### 400 Bad Request

**Symptoms:**
```json
{
  "detail": "Invalid asset type: INVALID_TYPE",
  "status_code": 400
}
```

**Solution:**
- Check request parameters
- Valid asset types: STOCK, CRYPTO, METAL
- Valid transaction types: BUY, SELL, STAKING, AIRDROP, MINING, DIVIDEND

---

### Connection timeout

**Symptoms:**
```
ConnectionError: ('Connection aborted.', timeout('timed out'))
```

**Solution:**
```bash
# 1. Check backend is running
docker-compose ps backend

# 2. Check firewall
sudo ufw status

# 3. Increase timeout
# Edit request timeout in frontend/src/api.ts
```

---

## Frontend Issues

### White screen / blank page

**Symptoms:**
- Frontend loads but shows nothing
- Browser console shows errors

**Solution:**
```bash
# 1. Check browser console (F12)
# Look for JavaScript errors

# 2. Clear browser cache
# Ctrl+Shift+R (hard refresh)

# 3. Rebuild frontend
docker-compose restart frontend

# 4. Check frontend logs
make logs-frontend
```

---

### Hot reload not working

**Symptoms:**
- Code changes don't appear
- Must refresh manually

**Solution:**
```bash
# 1. Check file watching
make logs-frontend | grep "HMR"

# 2. Restart frontend
docker-compose restart frontend

# 3. Check volume mounts
docker inspect portfolio-management-frontend-1 | grep Mounts -A 20
```

---

### API calls failing (CORS)

**Symptoms:**
```
Access to fetch at 'http://localhost:8000/api/portfolio/summary' from origin 'http://localhost:3003' has been blocked by CORS policy
```

**Solution:**
```bash
# 1. Check CORS configuration in backend/main.py
# Should allow localhost:3003

# 2. Check VITE_API_URL
echo $VITE_API_URL
# Should be: http://localhost:8000

# 3. Restart backend
docker-compose restart backend
```

---

## Recovery Procedures

### Complete Reset (Nuclear Option)

**When to use:**
- Everything is broken
- No other solutions work
- Fresh start needed

**Steps:**
```bash
# 1. Backup data (if needed)
make backup

# 2. Stop and remove everything
docker-compose down -v
docker system prune -a --volumes -f

# 3. Clean project
rm -rf backend/.venv
rm -rf frontend/node_modules
rm -rf backend/__pycache__
rm -rf backend/.pytest_cache

# 4. Fresh start
make dev

# 5. Restore data (if backed up)
make restore FILE=./backups/backup_YYYYMMDD.sql
```

---

### Partial Reset

**Reset database only:**
```bash
make db-reset
```

**Reset backend only:**
```bash
docker-compose rm -f backend
docker-compose build backend
docker-compose up backend
```

**Reset frontend only:**
```bash
docker-compose rm -f frontend
docker-compose build frontend
docker-compose up frontend
```

---

## Getting Help

### Before Asking for Help

1. **Check logs:**
   ```bash
   make logs > debug.log
   ```

2. **Check versions:**
   ```bash
   docker --version
   docker-compose --version
   python --version
   node --version
   ```

3. **Run diagnostics:**
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/api/import/status
   ```

### What to Include

When reporting issues:
- Error message (full text)
- Steps to reproduce
- Logs (relevant portion)
- Environment (OS, Docker version)
- What you've tried

### Where to Get Help

- **Documentation:** [docs/README.md](./README.md)
- **GitHub Issues:** https://github.com/your-repo/portfolio-management/issues
- **Logs:** Always check logs first (`make logs`)

---

## Quick Reference

### Most Common Issues

| Problem | Quick Fix |
|---------|-----------|
| Port in use | `lsof -i :8000` then `kill -9 <PID>` |
| Database won't connect | Check `.env` passwords match |
| Import fails | Check filename pattern |
| Prices not updating | `curl -X POST .../refresh-prices` |
| Slow performance | Increase Docker memory to 4GB |
| White screen | Clear browser cache (Ctrl+Shift+R) |
| Everything broken | `make clean-all && make dev` |

---

**Still stuck?** Check other docs:
- [QUICK-START.md](./QUICK-START.md) - Setup guide
- [CONFIGURATION.md](./CONFIGURATION.md) - Configuration help
- [COMMAND-REFERENCE.md](./COMMAND-REFERENCE.md) - All commands
