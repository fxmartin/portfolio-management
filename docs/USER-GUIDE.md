# User Guide

Complete guide to using the Portfolio Management application.

## Table of Contents

1. [Dashboard Overview](#dashboard-overview)
2. [Importing Transactions](#importing-transactions)
3. [Managing Transactions](#managing-transactions)
4. [Portfolio Tracking](#portfolio-tracking)
5. [AI-Powered Analysis](#ai-powered-analysis)
6. [Rebalancing Recommendations](#rebalancing-recommendations)
7. [Investment Strategy](#investment-strategy)
8. [Settings & Configuration](#settings--configuration)

---

## Dashboard Overview

The dashboard is your main view of portfolio health and performance.

### Portfolio Summary Card

**Total Portfolio Value**
- Sum of all open positions + cash balances
- Auto-refreshes every 60-120 seconds
- Click "Refresh Prices" for manual update

**Key Metrics:**
- **Total Investment Value**: Market value of all positions (no cash)
- **Total Cost Basis**: What you paid for your assets (FIFO-calculated)
- **Total P&L**: Unrealized + Realized gains/losses
- **Total P&L %**: Percentage return on cost basis
- **Day Change**: Today's value change (coming soon)
- **Cash Balances**: Available cash by currency

### Open Positions Card

Shows all currently held assets with:

| Column | Description |
|--------|-------------|
| **Symbol** | Ticker symbol (BTC, AAPL, MSTR, etc.) |
| **Name** | Full asset name |
| **Type** | STOCK, CRYPTO, or METAL |
| **Quantity** | Current holdings |
| **Avg Cost** | Average purchase price (FIFO) |
| **Current Price** | Latest market price |
| **Value** | Current market value (quantity × price) |
| **P&L** | Unrealized gain/loss |
| **P&L %** | Percentage gain/loss |
| **Portfolio %** | Percentage of total portfolio |

**Features:**
- Click any row to expand transaction details
- Sort by any column (click header)
- Auto-sorted by portfolio % (largest first)

### Realized P&L Card

Shows profit/loss from sold positions:

**Summary Metrics:**
- **Total Realized P&L**: Gains/losses from all sales
- **Total Fees**: All transaction fees (buy + sell)
- **Net P&L**: Realized P&L minus fees

**Breakdown by Asset Type:**
- Stocks: Sales from stock positions
- Crypto: Sales from cryptocurrency positions
- Metals: Sales from precious metals positions

**Transaction Details:**
Click "View Closed Transactions" to see:
- Sale date and quantity sold
- Buy price (FIFO average) vs. Sell price
- Gross P&L and fees
- Net P&L after fees

### Asset Allocation Chart

Pie chart showing portfolio distribution:
- Stocks (% and value)
- Crypto (% and value)
- Metals (% and value)

Hover over segments for detailed breakdown.

### Portfolio Performance Chart

Historical portfolio value over time:
- **Time Periods**: 1D, 1W, 1M, 3M, 1Y, All
- **Calculation**: Current quantities × historical prices
- **Shows**: How your CURRENT holdings performed over time

**Example:** If you hold 1074.52 AMEM today, the chart shows how that quantity's value changed historically.

---

## Importing Transactions

Import your trading history from CSV exports.

### Supported File Formats

#### 1. Revolut Metals (`account-statement_*.csv`)

**Filename pattern:** `account-statement_2024-11-01_2024-11-05.csv`

**What it contains:**
- Gold, Silver, and other precious metals trades
- Buy and sell transactions
- Fees included in total amount

**Required columns:**
- `Date Completed`: Transaction date
- `Description`: Transaction type and details
- `EUR AMOUNT`: Transaction amount in EUR

#### 2. Revolut Stocks (`[UUID].csv`)

**Filename pattern:** `c3e4f5a6-7b8c-9d0e-1f2a-3b4c5d6e7f8g.csv`

**What it contains:**
- Stock purchases and sales
- Dividends
- Fees as separate line items

**Required columns:**
- `Date`: Transaction date
- `Ticker`: Stock symbol
- `Type`: BUY, SELL, DIVIDEND
- `Quantity`: Number of shares
- `Price per share`: Unit price
- `Total Amount`: Total transaction value

#### 3. Koinly Crypto (`*koinly*.csv`)

**Filename pattern:** `portfolio_koinly_export_2024-11-01.csv`

**What it contains:**
- Cryptocurrency trades
- Staking rewards
- Airdrops
- Mining income

**Required columns:**
- `Date`: Transaction date
- `Sent Amount` / `Received Amount`: Quantities
- `Sent Currency` / `Received Currency`: Symbols
- `Fee Amount` / `Fee Currency`: Transaction fees
- `Label`: Transaction type (buy, sell, staking, etc.)

### How to Import

#### Step 1: Export Your Data

**From Revolut:**
1. Open Revolut app
2. Go to Account → Statements
3. Select date range
4. Download CSV

**From Koinly:**
1. Login to Koinly
2. Go to Tax Reports → Transactions
3. Export → CSV
4. Download file

#### Step 2: Upload to App

1. Click **"Import Transactions"** in sidebar
2. **Select files:**
   - Click "Choose Files" button
   - Or drag-and-drop onto the import area
3. **Multi-file support**: Upload multiple files at once
4. **Wait for processing**: Progress bar shows status

#### Step 3: Review Results

After import, you'll see:

**Summary:**
- Total files processed
- Successful imports
- Failed imports
- Total transactions saved

**Per-File Results:**
- Filename and detected type
- Transactions count
- Saved / Skipped / Failed counts
- Error messages (if any)

**Automatic Actions:**
- Positions recalculated with FIFO
- Portfolio summary updated
- P&L calculations refreshed

### Duplicate Handling

The app detects duplicates by:
- Symbol + Date + Quantity + Price

**Duplicate Strategies:**

1. **Skip** (default): Ignore duplicates, don't import
2. **Update**: Replace existing transaction with new data
3. **Force**: Import even if duplicate exists

**To check for duplicates before importing:**
```bash
curl -X POST http://localhost:8000/api/import/check-duplicates \
  -F "file=@your_file.csv"
```

### Common Import Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Invalid file type" | File doesn't match naming pattern | Rename file to match format |
| "File too large" | File exceeds 10MB limit | Split into smaller date ranges |
| "Missing required columns" | CSV structure changed | Check column names match expected format |
| "Invalid date format" | Date not parseable | Ensure dates are YYYY-MM-DD or DD/MM/YYYY |
| "Duplicate transactions" | Same transaction already exists | Use duplicate strategy or skip |

---

## Managing Transactions

View, create, edit, and delete individual transactions.

### Viewing All Transactions

Click **"Transactions"** in sidebar to see complete transaction history:

**Filters:**
- Asset Type: STOCK, CRYPTO, METAL, or All
- Transaction Type: BUY, SELL, STAKING, AIRDROP, MINING, CASH_IN, CASH_OUT
- Date Range: Start and end dates
- Symbol: Specific ticker

**Columns:**
- Date
- Symbol
- Type
- Quantity
- Price
- Fee
- Total Amount
- Currency
- Source File

### Adding Manual Transactions

Sometimes you need to add transactions manually (missing from CSV, manual trade, etc.).

**To add a transaction:**

1. Click **"Transactions"** → **"Add Transaction"**
2. Fill in the form:
   - **Date**: Transaction date (YYYY-MM-DD)
   - **Symbol**: Ticker symbol (BTC, AAPL, etc.)
   - **Type**: BUY, SELL, STAKING, etc.
   - **Quantity**: Amount bought/sold
   - **Price**: Price per unit
   - **Fee**: Transaction fee (optional)
   - **Currency**: EUR, USD, etc.
   - **Asset Type**: STOCK, CRYPTO, or METAL
3. Click **"Save"**

**Automatic Impact:**
- Positions recalculated immediately
- P&L updated
- Portfolio value refreshed

### Editing Transactions

**To edit:**
1. Click transaction row to expand details
2. Click **"Edit"** button
3. Modify fields
4. Click **"Save"**

**What you can edit:**
- Date, Symbol, Type, Quantity, Price, Fee, Currency

**What happens:**
- Position recalculated with new values
- Historical P&L updated
- Audit trail created (see transaction history)

### Deleting Transactions

**To delete:**
1. Click transaction row
2. Click **"Delete"** button
3. Confirm deletion

**⚠️ Warning:** Deletion impacts:
- Position quantities recalculated
- P&L updated
- FIFO lots affected
- Cannot be undone (unless restored from audit log)

**Check deletion impact before confirming:**
```bash
curl http://localhost:8000/api/transactions/{id}/impact
```

### Transaction History & Audit Trail

Every edit creates an audit entry showing:
- What changed
- When it changed
- Old value → New value

**To view history:**
```bash
curl http://localhost:8000/api/transactions/{id}/history
```

---

## Portfolio Tracking

Understand how your portfolio is calculated and tracked.

### FIFO Cost Basis

**What is FIFO?**
First-In, First-Out: When you sell, the oldest purchases are sold first.

**Example:**
```
Buy 10 BTC @ $30,000 = $300,000 (Jan 1)
Buy 5 BTC @ $40,000 = $200,000 (Feb 1)
Sell 12 BTC @ $50,000 = $600,000 (Mar 1)

FIFO Calculation:
- First 10 BTC sold: $50,000 - $30,000 = $20,000 profit × 10 = $200,000
- Next 2 BTC sold: $50,000 - $40,000 = $10,000 profit × 2 = $20,000
- Total realized P&L: $220,000
```

**Why FIFO?**
- Tax-compliant in most jurisdictions
- Fair representation of gains/losses
- Consistent with accounting standards

### Fee Handling

**Fees are included in cost basis:**
- Buy fee: Added to purchase cost
- Sell fee: Deducted from sale proceeds

**Example:**
```
Buy 1 BTC @ $30,000 + $10 fee = $30,010 cost basis
Sell 1 BTC @ $50,000 - $15 fee = $49,985 proceeds
Realized P&L: $49,985 - $30,010 = $19,975
```

**Fee Tracking:**
- Total fees shown in portfolio summary
- Per-position fee breakdown in holdings table
- Separate realized vs. unrealized fee tracking

### Multi-Currency Support

**Supported Currencies:**
- EUR (base currency)
- USD (converted to EUR for display)
- Other currencies (as-is, user must convert)

**USD → EUR Conversion:**
- Uses live EURUSD=X exchange rate from Yahoo Finance
- Cached for 1 hour to reduce API calls
- Applies to US stocks (MSTR) and crypto positions

**Example:**
```
MSTR position:
- Quantity: 19.68 shares
- Price: $381.50 (USD)
- Exchange rate: 1.0850 EURUSD
- Value in EUR: 19.68 × $381.50 ÷ 1.0850 = €6,915.18
```

### Price Updates

**Automatic Price Refresh:**
- Dashboard auto-refreshes every 60-120 seconds
- Fetches latest prices from Yahoo Finance
- Updates unrealized P&L
- Recalculates portfolio value

**Manual Refresh:**
Click **"Refresh Prices"** button to:
- Force immediate price update for all positions
- Bypass cache
- Update timestamp shown in UI

**Price Sources:**
1. **Yahoo Finance** (primary, free, unlimited)
2. **Twelve Data** (premium, historical data, European ETF coverage)
3. **Alpha Vantage** (fallback, free tier: 5 calls/min)
4. **CoinGecko** (crypto fundamentals, free tier)

### Position Recalculation

**When positions are recalculated:**
- After CSV import (automatic)
- After manual transaction add/edit/delete
- When clicking "Recalculate Positions" button

**What gets recalculated:**
- Current quantity (sum of buys - sells + rewards)
- Average cost basis (FIFO weighted average)
- Total cost basis (quantity × avg cost)
- Unrealized P&L (current value - cost basis)
- Unrealized P&L % (P&L ÷ cost basis × 100)

**Example Calculation:**
```
Transactions:
1. Buy 10 BTC @ $30,000 + $10 fee
2. Buy 5 BTC @ $40,000 + $5 fee
3. Sell 3 BTC @ $50,000 - $7 fee

FIFO Calculation:
- Sold 3 of the first 10 BTC lot
- Remaining: 7 BTC @ $30,001 + 5 BTC @ $40,001
- Quantity: 12 BTC
- Avg Cost: (7 × $30,001 + 5 × $40,001) ÷ 12 = $33,751
- Total Cost Basis: 12 × $33,751 = $405,012
```

---

## AI-Powered Analysis

Get insights from Claude AI about your portfolio and individual positions.

### Prerequisites

1. **Anthropic API Key** in `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
```

2. **Optional Market Data Keys** (enhances analysis):
```bash
TWELVE_DATA_API_KEY=...  # Historical data, European ETFs
ALPHA_VANTAGE_API_KEY=...  # US stock fundamentals
COINGECKO_API_KEY=...  # Crypto market data
```

### Global Market Analysis

**What it does:**
Analyzes entire portfolio with market context, sector insights, and risk assessment.

**To generate:**
1. Click **"Analysis"** in sidebar
2. View **"Global Market Analysis"** card
3. Click **"Generate Analysis"** if not cached

**Analysis includes:**
- Market sentiment (bullish, bearish, neutral)
- Macro-economic factors affecting your holdings
- Sector insights for stocks/ETFs you own
- Key risks to monitor
- Portfolio-level P&L context

**Data collected for analysis:**
- Total portfolio value and P&L
- Asset allocation breakdown
- Top 10 positions by value
- Recent market indicators
- Sector exposure
- Currency breakdown

**Performance:**
- First generation: 5-10 seconds
- Cached for: 24 hours
- Cost: ~$0.10-0.15 per analysis

### Position-Specific Analysis

**What it does:**
Deep dive into individual position with recommendations.

**To generate:**
1. Go to **Analysis** page
2. Scroll to **"Position Analysis"** section
3. Select symbol from dropdown
4. Click **"Analyze Position"**

**Analysis includes:**
- Current position status (quantity, P&L, cost basis)
- Recent price movement and trends
- Fundamental analysis (if data available)
- Technical indicators
- Risk assessment
- **Actionable recommendations**: HOLD, BUY_MORE, TRIM, SELL

**Data collected:**
- Position metrics (quantity, cost basis, P&L)
- Current price and historical prices (253 days if Twelve Data available)
- Volume and volatility
- Sector and industry (for stocks)
- Market cap and fundamentals (if available)
- Portfolio percentage
- Recent transactions

**Performance:**
- First generation: 3-5 seconds
- Cached for: 24 hours
- Cost: ~$0.05-0.08 per position

### Two-Quarter Forecast

**What it does:**
Predicts Q1 and Q2 performance with three scenarios.

**To generate:**
1. Analysis page → **"Forecast"** section
2. Select symbol
3. Click **"Generate Forecast"**

**Forecast includes:**

**Q1 Predictions (3 months):**
- **Pessimistic**: Low-end price target + reasoning
- **Realistic**: Most likely price target + reasoning
- **Optimistic**: High-end price target + reasoning
- Confidence levels for each scenario

**Q2 Predictions (6 months):**
- Same three scenarios
- Longer-term outlook
- Confidence levels

**Overall Outlook:**
- Market conditions
- Catalysts to watch
- Risk factors

**Data collected:**
- Same as position analysis
- Plus: Historical volatility, momentum indicators, market correlations

**Performance:**
- First generation: 8-15 seconds
- Cached for: 24 hours
- Cost: ~$0.15-0.20 per forecast

### Bulk Analysis

**What it does:**
Analyze multiple positions at once (parallel execution).

**API endpoint:**
```bash
POST /api/analysis/positions/bulk
{
  "symbols": ["BTC", "ETH", "SOL", "AAPL", "MSTR"]
}
```

**Performance:**
- 5 positions: ~15-30 seconds (parallel)
- Maximum: 10 positions per request
- Cost: ~$0.40-0.80 for 10 positions

### Cost Optimization

**Caching Strategy:**
- Global analysis: 24 hours
- Position analysis: 24 hours
- Forecasts: 24 hours
- Historical data: 1 hour
- Live prices: 1 minute

**Typical monthly cost** (with caching):
- 1 global analysis/day: ~$3.00
- 5 position analyses/day: ~$7.50
- 2 forecasts/week: ~$2.40
- **Total: ~$12.90/month**

**Without caching** (regenerate every time):
- Same usage: ~$450/month
- **Caching saves 97% of costs!**

### Customizing AI Prompts

**To customize prompts:**
1. Go to **Settings** → **AI Prompts**
2. Select prompt type:
   - Global Market Analysis
   - Position Recommendations
   - Two-Quarter Forecast
3. Click **"Edit"**
4. Modify template (supports Jinja2 syntax)
5. **Save** → Creates new version

**Prompt Variables Available:**

Global Analysis:
- `{{ total_value }}`, `{{ total_pnl }}`, `{{ positions }}`, `{{ market_indicators }}`

Position Analysis:
- `{{ symbol }}`, `{{ quantity }}`, `{{ cost_basis }}`, `{{ current_price }}`, `{{ pnl }}`, `{{ historical_prices }}`

Forecast:
- Same as position analysis + `{{ sector }}`, `{{ market_cap }}`

**Version History:**
- Every edit creates new version
- Restore previous versions anytime
- Compare versions side-by-side

---

## Rebalancing Recommendations

Get data-driven recommendations to align your portfolio with target allocations.

### Setting Target Allocations

1. Go to **Rebalancing** page
2. Choose rebalancing model:
   - **Equal Weight**: Each asset gets equal %
   - **60/40**: 60% stocks, 40% crypto/metals
   - **Risk Parity**: Balance risk across asset types
   - **Market Cap**: Weight by market capitalization
   - **Custom**: Define your own targets

3. Click **"Generate Recommendations"**

### Understanding Recommendations

**For each position, you'll see:**
- **Current Allocation**: % of portfolio
- **Target Allocation**: Desired %
- **Drift**: How far off target (percentage points)
- **Action**: BUY or SELL
- **Amount**: How much to trade (in EUR)
- **Shares**: Number of units to buy/sell

**Summary Metrics:**
- Total trades needed
- Total buy amount
- Total sell amount
- Estimated rebalancing cost (fees)

### Alignment Score

**What it is:**
Gauge showing how aligned your portfolio is with targets.

**Score ranges:**
- 90-100%: Excellent alignment (minimal drift)
- 75-89%: Good alignment (some drift)
- 50-74%: Moderate drift (rebalancing recommended)
- Below 50%: Significant drift (rebalancing needed)

**Calculation:**
```
Score = 100 - (sum of absolute drifts ÷ 2)

Example:
BTC: 40% current vs. 30% target = 10% drift
ETH: 20% current vs. 30% target = 10% drift
SOL: 10% current vs. 20% target = 10% drift
Total drift: 30%
Score: 100 - (30 ÷ 2) = 85% (Good)
```

### Comparison Charts

**Allocation Comparison:**
- Side-by-side bars showing current vs. target
- Visual drift indicators
- Click any bar to see details

### Applying Recommendations

**Manual approach:**
1. Review recommendations
2. Execute trades on your exchange
3. Import new transactions via CSV
4. Recalculate positions

**Automated approach** (coming soon):
- Direct exchange integration
- One-click rebalancing
- Automatic transaction logging

---

## Investment Strategy

Define and track your investment strategy with AI-powered recommendations.

### Creating Your Strategy

1. Go to **Strategy** page
2. Click **"Create Strategy"** or use template
3. Define allocations by asset type:

**Asset Type Targets:**
- **Stocks**: X% (e.g., 40%)
- **Crypto**: Y% (e.g., 50%)
- **Metals**: Z% (e.g., 10%)

**Risk Profile:**
- **Conservative**: Low volatility, capital preservation
- **Moderate**: Balanced growth and stability
- **Aggressive**: High growth, accept volatility

**Time Horizon:**
- Short-term (< 1 year)
- Medium-term (1-5 years)
- Long-term (5+ years)

4. **Save Strategy**

### Strategy Templates

**Pre-built templates:**

1. **Conservative Growth**
   - 60% Stocks, 30% Metals, 10% Crypto
   - Risk: Low
   - Horizon: Long-term

2. **Balanced**
   - 50% Stocks, 40% Crypto, 10% Metals
   - Risk: Moderate
   - Horizon: Medium-term

3. **Aggressive Growth**
   - 30% Stocks, 60% Crypto, 10% Metals
   - Risk: High
   - Horizon: Long-term

4. **All Crypto**
   - 100% Crypto
   - Risk: Very High
   - Horizon: Short/Medium-term

**To use template:**
1. Click **"Templates"**
2. Select template
3. Click **"Apply"**
4. Customize if needed
5. Save

### Strategy-Driven Recommendations

**What it does:**
Compares current portfolio to your defined strategy and recommends actions.

**To generate:**
1. Ensure strategy is saved
2. Click **"Get Recommendations"**
3. Review AI-generated advice

**Recommendations include:**
- Asset allocation adjustments needed
- Specific positions to buy/sell
- Amount to trade per position
- Reasoning for each recommendation
- Risk assessment of current vs. target
- Tax implications (if applicable)

**Data provided to AI:**
- Your defined strategy (targets, risk, horizon)
- Current portfolio allocation
- Individual position performance
- Market conditions
- Historical trends

**Performance:**
- Generation time: 10-15 seconds
- Cached for: 24 hours
- Cost: ~$0.20-0.30 per analysis

### Streaming Recommendations

**Real-time generation:**
Watch recommendations being generated live.

**To use:**
```bash
curl -N http://localhost:8000/api/strategy/recommendations/stream
```

Or in the UI, click **"Stream Recommendations"** for live updates.

---

## Settings & Configuration

Customize app behavior and manage integrations.

### Settings Categories

#### 1. Currency & Format Settings

**Base Currency:**
- Select your preferred base currency (EUR default)
- All portfolio values display in base currency
- USD positions auto-converted to base

**Number Format:**
- Decimal separator (. or ,)
- Thousands separator (, or .)
- Decimal places for display

**Date Format:**
- DD/MM/YYYY (European)
- MM/DD/YYYY (American)
- YYYY-MM-DD (ISO)

#### 2. API Keys

**Anthropic Claude:**
- Required for AI analysis features
- Get key: https://console.anthropic.com/
- Cost: ~$12-15/month with caching
- Rate limit: 5000 tokens/min

**Twelve Data:**
- Historical prices for European ETFs
- Get key: https://twelvedata.com/
- Cost: $29/month (253 days historical data)
- Rate limit: 8 calls/min, 800 calls/day

**Alpha Vantage:**
- Fallback for US stock fundamentals
- Get key: https://www.alphavantage.co/
- Cost: Free tier (5 calls/min, 100 calls/day)

**CoinGecko:**
- Crypto market data and fundamentals
- Get key: https://www.coingecko.com/api
- Cost: Free tier or Demo tier
- Rate limit: 10-50 calls/min depending on tier

**To add/update API key:**
1. Go to Settings → API Keys
2. Paste key in input field
3. Click **"Save"**
4. Keys are encrypted at rest in database
5. Click "Reveal" to view masked key

#### 3. System Performance

**Cache Settings:**
- Historical data TTL (1 hour default)
- Quote data TTL (1 minute default)
- Forecast cache TTL (24 hours default)

**Price Refresh:**
- Auto-refresh interval (60-120 seconds)
- Batch size for price updates
- Fallback provider priority

**Database:**
- Connection pool size
- Query timeout
- Index optimization (auto)

#### 4. AI Prompts

**Manage AI prompt templates:**
- View all prompts
- Edit prompt templates
- Create new versions
- Restore previous versions
- Export/import prompts

**Prompt Variables:**
Each prompt has access to specific data variables (see AI Analysis section).

#### 5. Security Settings

**Encryption Key:**
- 44-character Fernet key for sensitive data
- Rotate every 90 days recommended
- Backup this key securely!

**Session Management:**
- Session timeout (future feature)
- API key rotation schedule

### Encryption & Security

**What's encrypted:**
- API keys in database
- Sensitive settings

**Encryption key setup:**
```bash
# Generate new key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Add to .env (use the generated key from above command)
SETTINGS_ENCRYPTION_KEY=your_generated_encryption_key_here
```

**Key rotation:**
```bash
cd backend
python rotate_encryption_key.py "OLD_KEY" "NEW_KEY"
```

### Backup & Restore Settings

**Backup all settings:**
```bash
GET /api/settings/export
```

**Restore from backup:**
```bash
POST /api/settings/import
{
  "settings": { ... }
}
```

**Resetting to defaults:**
```bash
POST /api/settings/reset-defaults
```

---

## Tips & Best Practices

### Import Best Practices

1. **Export by month**: Smaller files process faster
2. **Check for duplicates**: Use duplicate check endpoint first
3. **Backup before large import**: Use `make backup`
4. **Import oldest first**: Build position history chronologically

### Performance Tips

1. **Use caching**: Don't force-refresh unnecessarily
2. **Limit bulk operations**: Max 10 positions at once
3. **Off-peak API calls**: Generate forecasts overnight
4. **Monitor rate limits**: Check `/monitoring/market-data`

### Cost Optimization

1. **Enable all caching**: Reduces API calls by 95%+
2. **Use free tier first**: Yahoo Finance for prices
3. **Batch operations**: Bulk analysis instead of individual
4. **Review before generate**: Check cache timestamps first

### Portfolio Management

1. **Regular imports**: Weekly CSV imports keep data fresh
2. **Manual transactions**: Add missing trades immediately
3. **Verify P&L**: Compare with exchange reports quarterly
4. **Rebalance periodically**: Monthly or quarterly review
5. **Update strategy**: Adjust targets as goals change

---

**Need more help?** See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) or [API-REFERENCE.md](./API-REFERENCE.md).
