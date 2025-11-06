# Quick Start Guide

Get your portfolio tracker up and running in under 5 minutes.

## Prerequisites

Before you start, make sure you have:

- ✅ **Docker** installed ([Get Docker](https://docs.docker.com/get-docker/))
- ✅ **Docker Compose** installed (included with Docker Desktop)
- ✅ **CSV export files** from Revolut or Koinly (optional for initial setup)

**System Requirements:**
- 4GB RAM minimum
- 2GB free disk space
- macOS, Linux, or Windows with WSL2

## Installation (5 Minutes)

###  Step 1: Clone the Repository

```bash
git clone https://github.com/your-repo/portfolio-management.git
cd portfolio-management
```

### Step 2: Set Up Environment Variables

Copy the example environment file and configure your credentials:

```bash
cp .env.example .env
```

**Edit `.env` with your preferred editor:**
```bash
nano .env  # or: code .env, vim .env
```

**Minimum required changes:**
```bash
# Change the default database password (IMPORTANT!)
POSTGRES_PASSWORD=your_secure_password_here

# Update the database URL with your new password
DATABASE_URL=postgresql://trader:your_secure_password_here@postgres:5432/portfolio
```

**Optional API keys** (add later if needed):
```bash
# For AI-powered analysis (Epic 8)
ANTHROPIC_API_KEY=sk-ant-api03-...

# For market data fallback
ALPHA_VANTAGE_API_KEY=your_key_here

# For premium historical data (recommended)
TWELVE_DATA_API_KEY=your_key_here
```

> **Tip:** You can run the app without API keys. AI features will be disabled, but portfolio tracking and Yahoo Finance price data will work fine.

### Step 3: Start the Application

```bash
make dev
```

**This command will:**
- Download Docker images (~500MB first time)
- Start PostgreSQL, Redis, Backend, and Frontend
- Initialize the database schema
- Start hot-reload development servers

**Expected output:**
```
✓ Database ready on port 5432
✓ Redis ready on port 6379
✓ Backend API ready on http://localhost:8000
✓ Frontend app ready on http://localhost:3003
```

**First startup takes 2-3 minutes. Subsequent starts take ~10 seconds.**

### Step 4: Access the Application

Open your browser and navigate to:

🌐 **http://localhost:3003**

You should see the Portfolio Management dashboard.

## First Steps

### Import Your First Transaction File

1. **Click "Import Transactions"** in the sidebar
2. **Select your CSV file(s):**
   - Revolut Metals: `account-statement_*.csv`
   - Revolut Stocks: `[UUID].csv`
   - Koinly Crypto: `*koinly*.csv`
3. **Drag and drop** or **click to browse**
4. **Wait for processing** (5-10 seconds per file)
5. **View results** - Shows saved, skipped, and failed transactions

### View Your Portfolio

After importing, click **"Dashboard"** in the sidebar to see:

- 💰 **Total Portfolio Value** (all assets + cash)
- 📊 **Open Positions** (current holdings with P&L)
- 📈 **Asset Allocation** (stocks, crypto, metals breakdown)
- 🎯 **Realized P&L** (gains/losses from sales)

### Refresh Live Prices

Click the **"Refresh Prices"** button on the dashboard to:
- Fetch latest market prices from Yahoo Finance
- Update unrealized P&L for all positions
- Recalculate portfolio value

**Prices auto-refresh** every 60-120 seconds when the dashboard is open.

## Quick Commands

```bash
# Start all services
make dev

# Stop all services
make clean

# View logs
make logs

# Run tests
make test

# Access database shell
make shell-db

# Access backend shell
make shell-backend

# See all available commands
make help
```

## Verify Everything Works

### Test 1: Health Check
```bash
curl http://localhost:8000/health
```
Expected: `{"status":"healthy"}`

### Test 2: API Check
```bash
curl http://localhost:8000/api/import/status
```
Expected: JSON with supported CSV formats

### Test 3: Frontend Check
Open http://localhost:3003 - Should load without errors

## Common Issues

### Port Already in Use

**Symptoms:** `Error: Port 8000 is already allocated`

**Solution:**
```bash
# Stop the conflicting service
docker ps  # Find container using the port
docker stop <container-id>

# Or change the port in docker-compose.yml
```

### Database Connection Failed

**Symptoms:** `FATAL: password authentication failed`

**Solution:**
```bash
# Reset the database
make clean-all  # ⚠️ Deletes all data!
make dev
```

### Out of Memory

**Symptoms:** Container crashes, sluggish performance

**Solution:**
- Increase Docker Desktop memory to 4GB+ (Settings → Resources)
- Close other memory-intensive applications

## Next Steps

Once you're up and running:

1. **Import more files** - [CSV Import Guide](./CSV-IMPORT-GUIDE.md)
2. **Explore features** - [User Guide](./USER-GUIDE.md)
3. **Configure settings** - [Configuration Guide](./CONFIGURATION.md)
4. **Set up AI analysis** - [AI Analysis Docs](./AI_ANALYSIS.md)
5. **Customize prompts** - Settings → AI Prompts

## Getting Help

- 📖 **Full documentation**: [docs/README.md](./README.md)
- 🐛 **Report issues**: [GitHub Issues](https://github.com/your-repo/portfolio-management/issues)
- 💬 **Ask questions**: Check existing documentation first
- 🔧 **Troubleshooting**: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

## Security Reminder

⚠️ **Before going to production:**
- Change the default database password
- Never commit `.env` to version control
- Rotate API keys every 90 days
- See [SECURITY.md](./SECURITY.md) for full guide

---

**You're all set!** Import your first CSV and start tracking your portfolio.
