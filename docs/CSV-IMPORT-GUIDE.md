# CSV Import Guide

Complete reference for importing transaction data from CSV exports.

## Table of Contents

1. [Overview](#overview)
2. [Revolut Metals Format](#revolut-metals-format)
3. [Revolut Stocks Format](#revolut-stocks-format)
4. [Koinly Crypto Format](#koinly-crypto-format)
5. [File Naming Requirements](#file-naming-requirements)
6. [Import Process](#import-process)
7. [Troubleshooting](#troubleshooting)

---

## Overview

The Portfolio Management app supports three CSV formats:

| Format | Source | Assets | Detection |
|--------|--------|---------|-----------|
| **Revolut Metals** | Revolut App → Metals Account | Gold, Silver, Platinum, Palladium | Filename starts with `account-statement_` |
| **Revolut Stocks** | Revolut App → Stocks Portfolio | Stocks, ETFs | Filename is UUID format |
| **Koinly Crypto** | Koinly Export | Cryptocurrencies | Filename contains `koinly` |

**File size limit:** 10MB per file
**Multi-file support:** Upload multiple CSV files at once
**Duplicate detection:** Automatic (skips by default)

---

## Revolut Metals Format

### How to Export

1. Open **Revolut** app
2. Go to **Account** → **Commodities**
3. Tap **Statements**
4. Select date range
5. **Download CSV**

### File Naming

**Pattern:** `account-statement_YYYY-MM-DD_YYYY-MM-DD.csv`

**Examples:**
```
account-statement_2024-01-01_2024-01-31.csv ✅
account-statement_2024-11-01_2024-11-05.csv ✅
my_metals_export.csv ❌ (won't be detected)
```

### Required Columns

| Column Name | Description | Example |
|-------------|-------------|---------|
| **Type** | Transaction type | `Exchange` |
| **Product** | Product type | `Commodities` |
| **Started Date** | When transaction started | `2025-06-15 10:00:42` |
| **Completed Date** | When transaction completed | `2025-06-15 10:00:42` |
| **Description** | Human-readable description | `Exchanged to Gold` |
| **Amount** | Quantity of metal (+/- for buy/sell) | `0.082566` |
| **Fee** | Transaction fee | `0.000500` |
| **Currency** | Metal symbol or EUR | `XAU`, `EUR` |
| **State** | Transaction status | `COMPLETED` |
| **Balance** | Balance after transaction | `0.082566` |

### Supported Metals

| Symbol | Metal | Example Amount |
|--------|-------|----------------|
| **XAU** | Gold | `0.082566` troy oz |
| **XAG** | Silver | `12.490514` troy oz |
| **XPT** | Platinum | `0.184237` troy oz |
| **XPD** | Palladium | `0.163823` troy oz |

### Transaction Detection Logic

**Buy Transaction:**
- `Type` = `Exchange`
- `State` = `COMPLETED`
- `Amount` > 0 (positive)
- `Currency` = Metal symbol (XAU, XAG, XPT, XPD)
- Quantity = Amount - Fee

**Sell Transaction:**
- `Type` = `Exchange`
- `State` = `COMPLETED`
- `Amount` < 0 (negative)
- `Currency` = Metal symbol
- Quantity = |Amount|

### EUR Amount Mapping

**Important:** Revolut metals CSV doesn't include EUR amounts directly. The app uses a pre-configured mapping for accurate P&L calculations.

**If your transactions aren't in the mapping**, the P&L may be incorrect. Contact support to add your transactions to the mapping.

### Example Row

```csv
Type,Product,Started Date,Completed Date,Description,Amount,Fee,Currency,State,Balance
Exchange,Commodities,2025-06-15 10:00:42,2025-06-15 10:00:42,Exchanged to Gold,0.082566,0.000050,XAU,COMPLETED,0.082566
```

**Parsed as:**
- Transaction Type: BUY
- Asset Type: METAL
- Symbol: XAU
- Quantity: 0.082566 oz
- Fee: 0.000050 XAU
- Date: 2025-06-15 10:00:42
- EUR Amount: €250.00 (from mapping)
- Price per oz: €250.00 ÷ 0.082566 = €3,027.76

---

## Revolut Stocks Format

### How to Export

1. Open **Revolut** app
2. Go to **Invest** → **Portfolio**
3. Tap **Activity** or **Statements**
4. Select date range
5. **Download CSV**

### File Naming

**Pattern:** `[UUID].csv` (8-4-4-4-12 hex format)

**Examples:**
```
C3E4F5A6-7B8C-9D0E-1F2A-3B4C5D6E7F8G.csv ✅
a1b2c3d4-e5f6-7890-abcd-ef1234567890.csv ✅
my_stocks.csv ❌ (won't be detected)
```

### Required Columns

| Column Name | Description | Example |
|-------------|-------------|---------|
| **Date** | Transaction date | `2024-11-01T14:30:00Z` or `2024-11-01` |
| **Ticker** | Stock symbol | `AAPL`, `MSTR`, `AMEM.BE` |
| **Type** | Transaction type | `BUY - MARKET`, `SELL - MARKET`, `DIVIDEND` |
| **Quantity** | Number of shares | `10.5` |
| **Price per share** | Unit price | `$381.50` or `€100.25` |
| **Total Amount** | Total transaction value | `$4,005.75` or `€1,052.63` |
| **Currency** | Currency code | `USD`, `EUR` |
| **FX Rate** | Exchange rate (optional) | `1.0850` |

### Supported Transaction Types

| Type in CSV | Parsed As | Description |
|-------------|-----------|-------------|
| `BUY - MARKET` | BUY | Market buy order |
| `BUY - LIMIT` | BUY | Limit buy order |
| `SELL - MARKET` | SELL | Market sell order |
| `SELL - LIMIT` | SELL | Limit sell order |
| `DIVIDEND` | DIVIDEND | Dividend payment |
| `CASH TOP-UP` | SKIPPED | Cash deposit (ignored) |

### Notes

- **Fees:** Not shown separately in Revolut stocks export (assumed $0)
- **Thousands separators:** Commas in amounts are handled (`$1,234.56`)
- **Currency symbols:** Removed automatically (`€`, `$`, `£`)
- **Time zones:** ISO format with `Z` (UTC) supported

### Example Rows

**Buy transaction:**
```csv
Date,Ticker,Type,Quantity,Price per share,Total Amount,Currency,FX Rate
2024-11-01T14:30:00Z,MSTR,BUY - MARKET,19.68,$381.50,$7,507.92,USD,1.0850
```

**Parsed as:**
- Transaction Type: BUY
- Asset Type: STOCK
- Symbol: MSTR
- Quantity: 19.68 shares
- Price: $381.50 per share
- Total: $7,507.92
- Fee: $0.00
- Date: 2024-11-01 14:30:00

**Dividend transaction:**
```csv
Date,Ticker,Type,Quantity,Price per share,Total Amount,Currency,FX Rate
2024-10-15,AAPL,DIVIDEND,,$0.24,$2.40,USD,1.0850
```

**Parsed as:**
- Transaction Type: DIVIDEND
- Symbol: AAPL
- Amount: $2.40
- Quantity: Not applicable

---

## Koinly Crypto Format

### How to Export

1. Login to **Koinly** (https://koinly.io)
2. Go to **Tax Reports** → **Transactions**
3. Click **Export** → **CSV**
4. Download file

### File Naming

**Pattern:** Filename must contain `koinly` (case-insensitive)

**Examples:**
```
portfolio_koinly_export_2024-11-01.csv ✅
Koinly_Transactions_October.csv ✅
My_Koinly_Data.csv ✅
crypto_trades.csv ❌ (won't be detected)
```

### Supported Formats

Koinly has **two export formats** - both are supported:

#### Format 1: New Format (Recommended)

**Required columns:**
- `Date (UTC)` - Transaction timestamp
- `Type` - Transaction type
- `From Amount` / `From Currency` - Sent amount
- `To Amount` / `To Currency` - Received amount
- `Fee Amount` / `Fee Currency` - Transaction fee
- `Net Value (read-only)` / `Value Currency (read-only)` - Fiat value
- `TxHash` - Transaction hash (optional)
- `Description` - Transaction description

#### Format 2: Old Format (Legacy)

**Required columns:**
- `Date` - Transaction timestamp
- `Type` - Transaction type
- `In Amount` / `In Currency` - Received amount
- `Out Amount` / `Out Currency` - Sent amount (for sells)
- `Fee Amount` / `Fee Currency` - Transaction fee

### Transaction Type Mapping

| Koinly Type | Parsed As | Description |
|-------------|-----------|-------------|
| `buy` | BUY | Bought crypto with fiat |
| `sell` | SELL | Sold crypto for fiat |
| `trade` / `swap` | BUY | Crypto-to-crypto trade |
| `staking` / `reward` | STAKING | Staking rewards |
| `airdrop` | AIRDROP | Airdrop tokens |
| `mining` | MINING | Mining income |
| `fork` | AIRDROP | Hard fork tokens |
| `interest` | STAKING | Interest earned |

### Fiat Currencies (Ignored)

When looking for crypto amounts, these fiat currencies are ignored:
- USD, EUR, GBP, CAD, AUD, JPY, CHF, CNY

### Transaction Detection Logic

**Buy (Crypto received):**
- `To Amount` > 0 and `To Currency` is crypto
- Or: `In Amount` > 0 and `In Currency` is crypto
- Fee deducted from received amount

**Sell (Crypto sent):**
- `From Amount` > 0 and `From Currency` is crypto
- Or: `Out Amount` > 0 and `Out Currency` is crypto
- Fee added to sent amount

**Staking/Airdrop/Mining (Rewards):**
- `Type` = staking, airdrop, mining, reward, interest, fork
- Only received amount is recorded (no cost basis)

**Trades (Swap):**
- Two transactions created:
  1. SELL the sent crypto
  2. BUY the received crypto

### Example Rows (New Format)

**Buy transaction:**
```csv
Date (UTC),Type,From Amount,From Currency,To Amount,To Currency,Fee Amount,Fee Currency,Net Value (read-only),Value Currency (read-only),TxHash,Description
2024-10-22 17:00:00,buy,,EUR,0.1234,BTC,0.0005,BTC,-4500.00,EUR,abc123,Bought BTC
```

**Parsed as:**
- Transaction Type: BUY
- Asset Type: CRYPTO
- Symbol: BTC
- Quantity: 0.1234 BTC
- Fee: 0.0005 BTC
- Total Cost: €4,500.00
- Price: €4,500 ÷ 0.1234 = €36,464.97 per BTC

**Staking reward:**
```csv
Date (UTC),Type,From Amount,From Currency,To Amount,To Currency,Fee Amount,Fee Currency,Net Value (read-only),Value Currency (read-only),TxHash,Description
2024-10-22 12:00:00,staking,,,0.0141,SOL,,,150.00,EUR,xyz789,Staking reward
```

**Parsed as:**
- Transaction Type: STAKING
- Symbol: SOL
- Quantity: 0.0141 SOL
- Fee: €0.00
- Value: €150.00

**Crypto swap (trade):**
```csv
Date (UTC),Type,From Amount,From Currency,To Amount,To Currency,Fee Amount,Fee Currency,Net Value (read-only),Value Currency (read-only),TxHash,Description
2024-10-20 15:30:00,trade,1.5,ETH,0.05,BTC,0.0001,BTC,0.00,EUR,def456,Swapped ETH for BTC
```

**Parsed as two transactions:**
1. SELL 1.5 ETH
2. BUY 0.05 BTC (fee: 0.0001 BTC)

### Example Rows (Old Format)

**Buy transaction:**
```csv
Date,Type,In Amount,In Currency,Out Amount,Out Currency,Fee Amount,Fee Currency
2024-10-22 17:00:00,buy,0.1234,BTC,4500.00,EUR,0.0005,BTC
```

**Staking reward:**
```csv
Date,Type,In Amount,In Currency,Out Amount,Out Currency,Fee Amount,Fee Currency
2024-10-22 12:00:00,staking,0.0141,SOL,,,,
```

---

## File Naming Requirements

### Detection Rules

The app auto-detects file type based on filename:

```
Filename                                → Detected Type
─────────────────────────────────────────────────────
account-statement_2024-11-01.csv        → METALS ✅
C3E4F5A6-7B8C-9D0E-1F2A-3B4C5D6E7F8G.csv → STOCKS ✅
portfolio_koinly_export.csv             → CRYPTO ✅
my_trades.csv                           → UNKNOWN ❌
```

### Renaming Files

If your file isn't detected, rename it to match the pattern:

**For Revolut Metals:**
```bash
# Original name
mv revolut_metals_oct_2024.csv account-statement_2024-10-01_2024-10-31.csv

# Pattern
account-statement_[anything].csv
```

**For Revolut Stocks:**
```bash
# Original name
mv revolut_stocks.csv C3E4F5A6-7B8C-9D0E-1F2A-3B4C5D6E7F8G.csv

# Pattern (must be valid UUID format)
[8 hex]-[4 hex]-[4 hex]-[4 hex]-[12 hex].csv
```

**For Koinly Crypto:**
```bash
# Original name
mv crypto_export.csv my_koinly_export.csv

# Pattern (just needs "koinly" anywhere)
[anything]koinly[anything].csv
```

---

## Import Process

### Step-by-Step

1. **Navigate to Import Page**
   - Click "Import Transactions" in sidebar

2. **Select Files**
   - Click "Choose Files" button
   - Or drag-and-drop files onto the import area
   - Multiple files supported

3. **Review Detection**
   - App shows detected file type for each file
   - If "Unknown", check filename pattern

4. **Upload Files**
   - Click "Upload" button
   - Progress bar shows processing status

5. **Review Results**
   - **Summary:**
     - Total files processed
     - Successful imports
     - Failed imports
     - Total transactions saved

   - **Per-File Results:**
     - Filename
     - Detected type
     - Transactions count
     - Saved / Skipped / Failed
     - Error messages (if any)

6. **Automatic Actions**
   - Positions recalculated with FIFO
   - Portfolio summary updated
   - P&L calculations refreshed

### Duplicate Handling

**Default behavior:** Skip duplicates (don't import)

**Duplicate detection** by matching:
- Symbol
- Date
- Quantity
- Price

**Duplicate strategies:**

1. **Skip** (default):
   - Don't import duplicate transactions
   - Shows "skipped" count in results
   - No error raised

2. **Update**:
   - Replace existing transaction with new data
   - Useful for correcting mistakes

3. **Force**:
   - Import even if duplicate exists
   - Creates separate transaction
   - Use with caution!

**To set strategy:**
```bash
POST /api/import/upload?duplicate_strategy=skip|update|force
```

### Checking for Duplicates Before Import

**API endpoint:**
```bash
curl -X POST http://localhost:8000/api/import/check-duplicates \
  -F "file=@your_file.csv"
```

**Response:**
```json
{
  "filename": "account-statement_2024-11-01.csv",
  "file_type": "METALS",
  "total_transactions": 10,
  "duplicate_count": 2,
  "duplicates": [
    {
      "symbol": "XAU",
      "date": "2025-06-15T10:00:42",
      "quantity": 0.082566,
      "type": "BUY",
      "existing_id": 123,
      "existing_source": "account-statement_2024-10-01.csv"
    }
  ]
}
```

---

## Troubleshooting

### Common Errors

#### "Invalid file type"

**Cause:** Filename doesn't match expected pattern

**Solution:**
```bash
# Check filename
account-statement_2024-11-01.csv  ✅ METALS
C3E4F5A6-7B8C-9D0E-1F2A-3B4C5D6E7F8G.csv  ✅ STOCKS
portfolio_koinly_export.csv  ✅ CRYPTO
my_trades.csv  ❌ UNKNOWN

# Rename file to match pattern
mv my_trades.csv account-statement_my_trades.csv
```

#### "File too large"

**Cause:** File exceeds 10MB limit

**Solution:**
- Export smaller date ranges
- Split large file into chunks
- Remove unnecessary columns (keep required ones)

#### "Missing required columns"

**Cause:** CSV structure doesn't match expected format

**Solution:**
1. **Check column names** (case-sensitive):
   ```
   Metals: Type, Product, Started Date, Completed Date, Description, Amount, Fee, Currency, State, Balance
   Stocks: Date, Ticker, Type, Quantity, Price per share, Total Amount, Currency
   Crypto: Date (UTC), Type, From Amount, From Currency, To Amount, To Currency, Fee Amount, Fee Currency
   ```

2. **Re-export from source**:
   - Revolut/Koinly may have changed format
   - Use latest export version

3. **Check for BOM**:
   ```bash
   # Remove BOM if present
   sed '1s/^\xEF\xBB\xBF//' input.csv > output.csv
   ```

#### "Invalid date format"

**Cause:** Date not in expected format

**Expected formats:**
- **Metals:** `YYYY-MM-DD HH:MM:SS` (e.g., `2025-06-15 10:00:42`)
- **Stocks:** `YYYY-MM-DDTHH:MM:SSZ` or `YYYY-MM-DD`
- **Crypto:** `YYYY-MM-DD HH:MM:SS`

**Solution:**
- Don't modify date columns manually
- Re-export from source
- Ensure locale settings are correct in export

#### "Empty CSV file"

**Cause:** File has no data rows (only headers)

**Solution:**
- Check export date range has transactions
- Ensure export completed successfully
- Try re-exporting

#### "Duplicate transactions"

**Cause:** Same transactions already imported

**Solution:**
1. **Check before importing:**
   ```bash
   curl -X POST http://localhost:8000/api/import/check-duplicates \
     -F "file=@your_file.csv"
   ```

2. **Use duplicate strategy:**
   - `skip`: Ignore duplicates (default)
   - `update`: Replace existing
   - `force`: Import anyway

3. **Review existing transactions:**
   - Filter by date range
   - Check source file name
   - Delete duplicates manually if needed

### Validation Tips

**Before importing:**

1. **Open CSV in text editor** (not Excel - it can corrupt dates)
2. **Check first row** has column headers
3. **Check last row** has data (no trailing empty rows)
4. **Verify date format** matches expected
5. **Check for special characters** in amounts (remove currency symbols)

**Test with small file first:**
```bash
# Export just 1 week of data
# Import and verify results
# Then import full history
```

### Getting Help

**If import fails:**

1. **Check error message** in response
2. **Review file format** against this guide
3. **Test with example files** (see `/test-data` directory)
4. **Check logs:**
   ```bash
   make logs-backend
   ```

5. **Report issue:**
   - Include error message
   - Attach sample row (remove sensitive data)
   - Specify file type and source

---

## Quick Reference

### File Naming Patterns

```bash
# Revolut Metals
account-statement_*.csv

# Revolut Stocks
[UUID].csv (e.g., C3E4F5A6-7B8C-9D0E-1F2A-3B4C5D6E7F8G.csv)

# Koinly Crypto
*koinly*.csv (case-insensitive)
```

### Required Columns Summary

**Metals:** Type, Product, Started Date, Completed Date, Description, Amount, Fee, Currency, State, Balance

**Stocks:** Date, Ticker, Type, Quantity, Price per share, Total Amount, Currency

**Crypto (new):** Date (UTC), Type, From Amount, From Currency, To Amount, To Currency, Fee Amount, Fee Currency

**Crypto (old):** Date, Type, In Amount, In Currency, Out Amount, Out Currency, Fee Amount, Fee Currency

### API Endpoints

```bash
# Upload files
POST /api/import/upload

# Check duplicates
POST /api/import/check-duplicates

# Get supported formats
GET /api/import/status

# Get import summary
GET /api/import/summary?source_file=filename.csv
```

---

**Need more help?** See [USER-GUIDE.md](./USER-GUIDE.md) or [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
