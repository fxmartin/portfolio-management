# Configuration Guide

Complete reference for configuring the Portfolio Management application.

## Table of Contents

1. [Environment Variables](#environment-variables)
2. [Application Settings](#application-settings)
3. [Market Data Configuration](#market-data-configuration)
4. [Performance Tuning](#performance-tuning)
5. [Docker Configuration](#docker-configuration)

---

## Environment Variables

All configuration is managed through `.env` file in the project root.

### Setup

```bash
# Copy example file
cp .env.example .env

# Edit with your values
nano .env
```

### Database Configuration

```bash
# PostgreSQL database credentials
POSTGRES_USER=trader
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=portfolio

# Database connection URL (update password to match above)
DATABASE_URL=postgresql://trader:your_secure_password_here@postgres:5432/portfolio
```

**Security Notes:**
- ⚠️ **Change default password** before production
- Use 20+ character passwords
- Never commit `.env` to version control
- Rotate passwords every 90 days

---

### API Keys

#### Anthropic Claude (AI Analysis)

```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
```

**Purpose:** AI-powered market analysis and recommendations
**Required:** No (app works without it, AI features disabled)
**Cost:** ~$12-15/month with caching
**Get key:** https://console.anthropic.com/
**Rate limits:** 5000 tokens/min

---

#### Twelve Data (Historical Prices)

```bash
TWELVE_DATA_API_KEY=your_key_here
TWELVE_DATA_RATE_LIMIT_PER_MINUTE=8
TWELVE_DATA_RATE_LIMIT_PER_DAY=800
```

**Purpose:** Historical prices for European ETFs and stocks
**Required:** No (Yahoo Finance used as fallback)
**Cost:** $29/month (253 days historical data)
**Get key:** https://twelvedata.com/
**Rate limits:** 8 calls/min, 800 calls/day

**Benefits:**
- Better European ETF coverage
- 253 days historical data
- Fundamental data included
- Used for AI analysis quality

---

#### Alpha Vantage (Market Data Fallback)

```bash
ALPHA_VANTAGE_API_KEY=your_key_here
ALPHA_VANTAGE_RATE_LIMIT_PER_MINUTE=5
ALPHA_VANTAGE_RATE_LIMIT_PER_DAY=100
```

**Purpose:** Fallback for US stock fundamentals
**Required:** No (Yahoo Finance primary)
**Cost:** Free tier (5 calls/min, 100 calls/day)
**Get key:** https://www.alphavantage.co/support/#api-key
**Rate limits:** 5 calls/min, 100 calls/day (free tier)

**When it's used:**
- Yahoo Finance fails or returns no data
- Cryptocurrency price fetching (alternative)
- Circuit breaker pattern prevents excessive calls

---

#### CoinGecko (Crypto Fundamentals)

```bash
COINGECKO_API_KEY=  # Empty for free tier
COINGECKO_RATE_LIMIT_PER_MINUTE=10
```

**Purpose:** Cryptocurrency market data and fundamentals
**Required:** No
**Cost:** Free tier (10 calls/min) or Demo tier (50 calls/min)
**Get key:** https://www.coingecko.com/api (optional, works without key)
**Rate limits:** 10-50 calls/min depending on tier

---

### Settings Encryption

```bash
SETTINGS_ENCRYPTION_KEY=your_generated_encryption_key_here
```

**Purpose:** Encrypt sensitive settings stored in database
**Required:** Yes (for Epic 9 features)
**Generate:**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**⚠️ CRITICAL:**
- **Backup this key securely!** Lost key = unrecoverable encrypted data
- Store in password manager
- Rotate every 90 days
- Never commit to version control

**What's encrypted:**
- API keys in database settings
- Other sensitive configuration values

---

### Redis Configuration

```bash
REDIS_URL=redis://redis:6379
```

**Purpose:** Caching for market data and API responses
**Default:** redis://redis:6379 (Docker internal network)
**TTL Configuration:**
- Historical data: 1 hour
- Live quotes: 1 minute
- Forecasts: 24 hours

---

### Frontend Configuration

```bash
VITE_API_URL=http://localhost:8000
VITE_BASE_CURRENCY=EUR
```

**VITE_API_URL:** Backend API endpoint
**VITE_BASE_CURRENCY:** Display currency for portfolio values

---

### Complete Example

```bash
# .env file

# Database
POSTGRES_USER=trader
POSTGRES_PASSWORD=my_secure_password_12345
POSTGRES_DB=portfolio
DATABASE_URL=postgresql://trader:my_secure_password_12345@postgres:5432/portfolio

# Redis
REDIS_URL=redis://redis:6379

# AI Analysis (Optional)
ANTHROPIC_API_KEY=sk-ant-api03-...

# Market Data (Optional)
TWELVE_DATA_API_KEY=your_key_here
TWELVE_DATA_RATE_LIMIT_PER_MINUTE=8
TWELVE_DATA_RATE_LIMIT_PER_DAY=800

ALPHA_VANTAGE_API_KEY=your_key_here
ALPHA_VANTAGE_RATE_LIMIT_PER_MINUTE=5
ALPHA_VANTAGE_RATE_LIMIT_PER_DAY=100

COINGECKO_API_KEY=
COINGECKO_RATE_LIMIT_PER_MINUTE=10

# Settings Encryption
SETTINGS_ENCRYPTION_KEY=your_generated_encryption_key_here

# Frontend
VITE_API_URL=http://localhost:8000
VITE_BASE_CURRENCY=EUR
```

---

## Application Settings

Settings managed through UI or API (stored in database).

### Currency & Format Settings

**Access:** Settings → Currency & Format

| Setting | Default | Description |
|---------|---------|-------------|
| Base Currency | EUR | Display currency for portfolio |
| Decimal Separator | . | Number formatting |
| Thousands Separator | , | Number formatting |
| Decimal Places | 2 | Display precision |
| Date Format | DD/MM/YYYY | Date display format |

**Date Format Options:**
- `DD/MM/YYYY` (European)
- `MM/DD/YYYY` (American)
- `YYYY-MM-DD` (ISO)

---

### API Keys (UI Management)

**Access:** Settings → API Keys

All API keys can be managed through the settings UI:
- Add/update keys without touching `.env`
- Keys encrypted at rest in database
- Masked display (click "Reveal" to view)
- Validation on save

---

### System Performance Settings

**Access:** Settings → System Performance

| Setting | Default | Description |
|---------|---------|-------------|
| Cache TTL - Historical Data | 3600s (1hr) | How long to cache historical prices |
| Cache TTL - Quotes | 60s | How long to cache live quotes |
| Cache TTL - Forecasts | 86400s (24hr) | How long to cache AI forecasts |
| Auto-Refresh Interval | 60-120s | Dashboard price refresh frequency |
| Price Update Batch Size | 50 | Max symbols per price fetch |

---

### AI Prompt Templates

**Access:** Settings → AI Prompts

**Customizable prompts:**
1. **Global Market Analysis**
   - Template variables: `total_value`, `positions`, `market_indicators`
   - Default length: ~500 tokens

2. **Position Recommendations**
   - Template variables: `symbol`, `quantity`, `cost_basis`, `current_price`, `pnl`
   - Default length: ~400 tokens

3. **Two-Quarter Forecast**
   - Template variables: `symbol`, `historical_prices`, `sector`, `market_cap`
   - Default length: ~600 tokens

**Template Features:**
- Jinja2 syntax support
- Version history (restore previous versions)
- Side-by-side comparison
- Export/import templates

---

## Market Data Configuration

### Provider Priority Order

The app uses intelligent fallback between market data providers:

**For Live Prices:**
1. **Yahoo Finance** (primary, free, unlimited)
2. **Twelve Data** (if API key configured)
3. **Alpha Vantage** (if API key configured, circuit breaker protected)

**For Historical Data:**
1. **Twelve Data** (if API key configured, best European coverage)
2. **Yahoo Finance** (free fallback)
3. **Alpha Vantage** (emergency fallback)

**For Crypto Fundamentals:**
1. **CoinGecko** (free tier or Demo tier)
2. **Twelve Data** (if available)

### Circuit Breaker Pattern

**Alpha Vantage circuit breaker:**
- Opens after 5 consecutive failures
- Timeout: 5 minutes
- Prevents excessive calls when provider is down

**Monitor circuit breaker:**
```bash
curl http://localhost:8000/api/monitoring/market-data
```

### Rate Limit Management

**Token bucket algorithm:**
- Tracks calls per minute and per day
- Blocks requests when limit reached
- Automatic quota reset

**Check current usage:**
```bash
GET /api/monitoring/market-data
```

**Response shows:**
- Total calls made
- Current minute/day usage
- Quota percentage
- Warning when approaching limits (80%)

---

## Performance Tuning

### Cache Optimization

**Recommended TTL values:**

```bash
# For heavy usage (reduce API costs)
HISTORICAL_DATA_TTL=3600  # 1 hour
QUOTE_TTL=60  # 1 minute
FORECAST_TTL=86400  # 24 hours

# For real-time accuracy (higher API costs)
HISTORICAL_DATA_TTL=1800  # 30 minutes
QUOTE_TTL=30  # 30 seconds
FORECAST_TTL=43200  # 12 hours
```

**Cache hit rate monitoring:**
```bash
GET /api/monitoring/market-data
# Returns cache_hit_rate percentage
```

**Target:** 75%+ cache hit rate

---

### Database Connection Pool

**Default settings:**
```python
pool_size=5  # Concurrent connections
max_overflow=10  # Additional connections when busy
```

**For heavy load:**
```python
pool_size=10
max_overflow=20
```

---

### Docker Resource Limits

**Edit `docker-compose.yml`:**

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

**Recommended minimums:**
- Backend: 512MB RAM, 0.5 CPU
- Frontend: 256MB RAM, 0.25 CPU
- PostgreSQL: 512MB RAM, 0.5 CPU
- Redis: 256MB RAM, 0.25 CPU

---

## Docker Configuration

### Port Mapping

**Default ports:**
```yaml
services:
  backend:
    ports:
      - "8000:8000"
  frontend:
    ports:
      - "3003:3003"
  postgres:
    ports:
      - "5432:5432"
  redis:
    ports:
      - "6379:6379"
```

**Change ports if conflicts:**
```yaml
ports:
  - "9000:8000"  # Map external 9000 to internal 8000
```

---

### Volume Configuration

**Data persistence:**
```yaml
volumes:
  postgres_data:
    driver: local
```

**Backup volumes:**
```bash
docker run --rm -v postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres_data.tar.gz -C /data .
```

**Restore volumes:**
```bash
docker run --rm -v postgres_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/postgres_data.tar.gz -C /data
```

---

### Environment-Specific Overrides

**Development:**
```bash
make dev  # Uses docker-compose.yml + docker-compose.dev.yml
```

**Production:**
```bash
make prod  # Uses docker-compose.yml + docker-compose.prod.yml
```

---

## Security Best Practices

### Credential Rotation Schedule

| Credential | Rotation Frequency |
|------------|-------------------|
| Database Password | Every 90 days |
| API Keys | Every 90 days |
| Encryption Key | Every 90 days |
| Docker Secrets | Every 180 days |

### Audit Checklist

- [ ] `.env` is in `.gitignore`
- [ ] No credentials hardcoded in source
- [ ] Strong database password (20+ characters)
- [ ] Encryption key backed up securely
- [ ] API keys rotated regularly
- [ ] Docker secrets used in production
- [ ] SSL/TLS enabled for all external connections

---

## Troubleshooting Configuration

### Testing Configuration

**Test database connection:**
```bash
docker-compose exec backend python -c "from database import engine; print('DB OK')"
```

**Test Redis connection:**
```bash
docker-compose exec redis redis-cli ping
# Should return: PONG
```

**Test API keys:**
```bash
# Anthropic
curl http://localhost:8000/api/analysis/global

# Yahoo Finance (always works, no key needed)
curl http://localhost:8000/api/portfolio/refresh-prices
```

### Common Configuration Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Database connection failed | Wrong password in `DATABASE_URL` | Match `POSTGRES_PASSWORD` exactly |
| Redis connection failed | Wrong `REDIS_URL` | Use `redis://redis:6379` for Docker |
| API key invalid | Wrong key format | Re-copy key from provider |
| Encryption key error | Wrong key format | Must be 44-character Fernet key |
| Port already in use | Port conflict | Change port mapping in docker-compose.yml |

---

**Need more help?** See [SECURITY.md](./SECURITY.md) or [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
