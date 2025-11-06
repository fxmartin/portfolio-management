# API Reference

Complete REST API documentation for the Portfolio Management application.

## Base URL

```
Development: http://localhost:8000
Production: https://your-domain.com
```

## Table of Contents

1. [Authentication](#authentication)
2. [Import API](#import-api)
3. [Portfolio API](#portfolio-api)
4. [Transactions API](#transactions-api)
5. [Analysis API](#analysis-api)
6. [Rebalancing API](#rebalancing-api)
7. [Strategy API](#strategy-api)
8. [Settings API](#settings-api)
9. [Database API](#database-api)
10. [Monitoring API](#monitoring-api)
11. [Error Codes](#error-codes)

---

## Authentication

**Current version:** No authentication required (v1.0)

**Future versions:** Will require API key or OAuth2

---

## Import API

### Upload CSV Files

Import transaction files with automatic format detection.

**Endpoint:** `POST /api/import/upload`

**Request:**
```bash
curl -X POST http://localhost:8000/api/import/upload \
  -F "files=@account-statement_2024-11-01.csv" \
  -F "files=@C3E4F5A6-7B8C-9D0E-1F2A-3B4C5D6E7F8G.csv" \
  -F "files=@portfolio_koinly_export.csv"
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `allow_duplicates` | boolean | false | Skip duplicates without error |
| `duplicate_strategy` | string | "skip" | How to handle duplicates: "skip", "update", or "force" |

**Response:**
```json
{
  "summary": {
    "total_files": 3,
    "successful": 2,
    "partial": 1,
    "failed": 0,
    "total_transactions": 150,
    "total_saved": 145,
    "total_skipped": 5,
    "total_failed": 0,
    "duplicate_strategy": "skip",
    "positions_recalculated": 25
  },
  "files": [
    {
      "filename": "account-statement_2024-11-01.csv",
      "status": "success",
      "file_type": "METALS",
      "errors": [],
      "transactions_count": 10,
      "saved_count": 10,
      "skipped_count": 0,
      "failed_count": 0,
      "message": "Saved 10 transactions, skipped 0 duplicates, 0 failed"
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Files processed (check individual file status)
- `400 Bad Request` - No files uploaded or invalid parameters
- `500 Internal Server Error` - Server error during processing

---

### Check for Duplicates

Check for potential duplicate transactions before importing.

**Endpoint:** `POST /api/import/check-duplicates`

**Request:**
```bash
curl -X POST http://localhost:8000/api/import/check-duplicates \
  -F "file=@account-statement_2024-11-01.csv"
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
  ],
  "has_more": false
}
```

---

### Get Import Status

Get supported CSV formats and import capabilities.

**Endpoint:** `GET /api/import/status`

**Request:**
```bash
curl http://localhost:8000/api/import/status
```

**Response:**
```json
{
  "status": "ready",
  "supported_formats": [
    {
      "type": "METALS",
      "description": "Revolut metals account statement",
      "pattern": "account-statement_*.csv"
    },
    {
      "type": "STOCKS",
      "description": "Revolut stocks export",
      "pattern": "[UUID].csv"
    },
    {
      "type": "CRYPTO",
      "description": "Koinly crypto transactions",
      "pattern": "*Koinly*.csv"
    }
  ]
}
```

---

### Get Import Summary

Get summary of imported transactions from database.

**Endpoint:** `GET /api/import/summary`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source_file` | string | No | Filter by source filename |

**Request:**
```bash
curl "http://localhost:8000/api/import/summary?source_file=account-statement_2024-11-01.csv"
```

**Response:**
```json
{
  "total_transactions": 150,
  "by_type": {
    "BUY": 80,
    "SELL": 40,
    "STAKING": 20,
    "AIRDROP": 5,
    "DIVIDEND": 5
  },
  "by_asset_type": {
    "STOCK": 50,
    "CRYPTO": 90,
    "METAL": 10
  },
  "by_source_file": {
    "account-statement_2024-11-01.csv": 10,
    "portfolio_koinly_export.csv": 90,
    "C3E4F5A6-7B8C-9D0E-1F2A-3B4C5D6E7F8G.csv": 50
  }
}
```

---

## Portfolio API

### Get Portfolio Summary

Get comprehensive portfolio overview for dashboard.

**Endpoint:** `GET /api/portfolio/summary`

**Request:**
```bash
curl http://localhost:8000/api/portfolio/summary
```

**Response:**
```json
{
  "total_value": 45678.25,
  "cash_balances": {
    "EUR": 1234.56,
    "USD": 0.00
  },
  "total_cash": 1234.56,
  "total_investment_value": 44443.69,
  "total_cost_basis": 38500.00,
  "total_pnl": 5943.69,
  "total_pnl_percent": 15.43,
  "unrealized_pnl": 4500.00,
  "realized_pnl": 1443.69,
  "day_change": 0.00,
  "day_change_percent": 0.00,
  "positions_count": 5,
  "last_updated": "2025-11-06T18:30:00"
}
```

---

### Get All Positions

Get all positions with current prices and P&L.

**Endpoint:** `GET /api/portfolio/positions`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `asset_type` | string | No | Filter by STOCK, CRYPTO, or METAL |

**Request:**
```bash
curl "http://localhost:8000/api/portfolio/positions?asset_type=CRYPTO"
```

**Response:**
```json
[
  {
    "symbol": "BTC",
    "asset_name": "Bitcoin",
    "asset_type": "CRYPTO",
    "quantity": 0.5234,
    "avg_cost_basis": 35000.00,
    "total_cost_basis": 18319.00,
    "current_price": 42000.00,
    "current_value": 21982.80,
    "unrealized_pnl": 3663.80,
    "unrealized_pnl_percent": 20.00,
    "portfolio_percentage": 48.15,
    "currency": "EUR",
    "first_purchase_date": "2024-01-15",
    "last_transaction_date": "2024-10-22",
    "last_price_update": "2025-11-06T18:25:00",
    "total_fees": 25.50,
    "fee_transaction_count": 3
  }
]
```

---

### Get Position Transactions

Get all transactions for a specific symbol.

**Endpoint:** `GET /api/portfolio/positions/{symbol}/transactions`

**Request:**
```bash
curl http://localhost:8000/api/portfolio/positions/BTC/transactions
```

**Response:**
```json
[
  {
    "id": 123,
    "date": "2024-10-22T17:00:00",
    "type": "BUY",
    "quantity": 0.1234,
    "price": 36464.97,
    "fee": 5.00,
    "total_amount": 4505.00,
    "currency": "EUR",
    "asset_type": "CRYPTO"
  }
]
```

---

### Refresh All Prices

Fetch latest prices for all positions.

**Endpoint:** `POST /api/portfolio/refresh-prices`

**Request:**
```bash
curl -X POST http://localhost:8000/api/portfolio/refresh-prices
```

**Response:**
```json
{
  "status": "completed",
  "updated_count": 5,
  "failed_count": 0,
  "failed_symbols": [],
  "timestamp": "2025-11-06T18:30:00"
}
```

---

### Recalculate Positions

Recalculate all positions from transaction history using FIFO.

**Endpoint:** `POST /api/portfolio/recalculate-positions`

**Request:**
```bash
curl -X POST http://localhost:8000/api/portfolio/recalculate-positions
```

**Response:**
```json
{
  "status": "completed",
  "positions_count": 5,
  "symbols": ["BTC", "ETH", "SOL", "MSTR", "AMEM"],
  "timestamp": "2025-11-06T18:30:00"
}
```

---

### Get Open Positions Overview

Get summary of open positions (excludes cash and closed positions).

**Endpoint:** `GET /api/portfolio/open-positions`

**Request:**
```bash
curl http://localhost:8000/api/portfolio/open-positions
```

**Response:**
```json
{
  "total_value": 44443.69,
  "total_cost_basis": 38500.00,
  "unrealized_pnl": 5943.69,
  "unrealized_pnl_percent": 15.43,
  "breakdown": {
    "stocks": {
      "value": 12500.00,
      "pnl": 1500.00,
      "pnl_percent": 13.64
    },
    "crypto": {
      "value": 30000.00,
      "pnl": 4000.00,
      "pnl_percent": 15.38
    },
    "metals": {
      "value": 1943.69,
      "pnl": 443.69,
      "pnl_percent": 29.59
    }
  },
  "last_updated": "2025-11-06T18:25:00",
  "total_fees": 125.50,
  "fee_transaction_count": 15
}
```

---

### Get Portfolio History

Get historical portfolio values for charting.

**Endpoint:** `GET /api/portfolio/history`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `period` | string | "1M" | Time period: "1D", "1W", "1M", "3M", "1Y", "All" |

**Request:**
```bash
curl "http://localhost:8000/api/portfolio/history?period=1M"
```

**Response:**
```json
{
  "data": [
    {"date": "2024-10-06T00:00:00", "value": 42500.00},
    {"date": "2024-10-13T00:00:00", "value": 43200.00},
    {"date": "2024-10-20T00:00:00", "value": 44100.00},
    {"date": "2024-10-27T00:00:00", "value": 44800.00},
    {"date": "2024-11-03T00:00:00", "value": 45678.25}
  ],
  "period": "1M",
  "initial_value": 42500.00,
  "current_value": 45678.25,
  "change": 3178.25,
  "change_percent": 7.48
}
```

---

### Get Realized P&L Summary

Get realized gains/losses from all sell transactions.

**Endpoint:** `GET /api/portfolio/realized-pnl`

**Request:**
```bash
curl http://localhost:8000/api/portfolio/realized-pnl
```

**Response:**
```json
{
  "total_realized_pnl": 1443.69,
  "total_fees": 125.50,
  "net_pnl": 1318.19,
  "closed_positions_count": 8,
  "breakdown": {
    "stocks": {
      "realized_pnl": 500.00,
      "fees": 25.00,
      "net_pnl": 475.00,
      "closed_count": 2
    },
    "crypto": {
      "realized_pnl": 800.00,
      "fees": 80.50,
      "net_pnl": 719.50,
      "closed_count": 5
    },
    "metals": {
      "realized_pnl": 143.69,
      "fees": 20.00,
      "net_pnl": 123.69,
      "closed_count": 1
    }
  },
  "last_updated": "2025-11-06T18:30:00"
}
```

---

### Get Closed Transactions

Get all closed (sold) transactions for a specific asset type.

**Endpoint:** `GET /api/portfolio/realized-pnl/{asset_type}/transactions`

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `asset_type` | string | "stocks", "crypto", or "metals" |

**Request:**
```bash
curl http://localhost:8000/api/portfolio/realized-pnl/crypto/transactions
```

**Response:**
```json
[
  {
    "id": 456,
    "symbol": "ETH",
    "sell_date": "2024-10-15T14:30:00",
    "quantity": 1.5,
    "buy_price": 2500.00,
    "sell_price": 2800.00,
    "gross_pnl": 450.00,
    "sell_fee": 10.00,
    "net_pnl": 440.00,
    "currency": "EUR"
  }
]
```

---

## Transactions API

### Create Transaction

Manually add a new transaction.

**Endpoint:** `POST /api/transactions`

**Request:**
```bash
curl -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTC",
    "transaction_type": "BUY",
    "asset_type": "CRYPTO",
    "quantity": 0.1,
    "price_per_unit": 42000.00,
    "fee": 5.00,
    "currency": "EUR",
    "transaction_date": "2024-11-06T12:00:00"
  }'
```

**Response:**
```json
{
  "id": 789,
  "symbol": "BTC",
  "transaction_type": "BUY",
  "asset_type": "CRYPTO",
  "quantity": 0.1,
  "price_per_unit": 42000.00,
  "fee": 5.00,
  "total_amount": 4205.00,
  "currency": "EUR",
  "transaction_date": "2024-11-06T12:00:00",
  "created_at": "2024-11-06T18:30:00",
  "updated_at": "2024-11-06T18:30:00"
}
```

---

### Get All Transactions

List all transactions with optional filters.

**Endpoint:** `GET /api/transactions`

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `asset_type` | string | Filter by STOCK, CRYPTO, or METAL |
| `transaction_type` | string | Filter by BUY, SELL, STAKING, etc. |
| `symbol` | string | Filter by ticker symbol |
| `start_date` | date | Start of date range (YYYY-MM-DD) |
| `end_date` | date | End of date range (YYYY-MM-DD) |
| `limit` | integer | Max results (default: 100) |
| `offset` | integer | Pagination offset (default: 0) |

**Request:**
```bash
curl "http://localhost:8000/api/transactions?asset_type=CRYPTO&symbol=BTC&limit=10"
```

---

### Update Transaction

Edit an existing transaction.

**Endpoint:** `PUT /api/transactions/{transaction_id}`

**Request:**
```bash
curl -X PUT http://localhost:8000/api/transactions/789 \
  -H "Content-Type: application/json" \
  -d '{
    "quantity": 0.15,
    "price_per_unit": 41000.00
  }'
```

---

### Delete Transaction

Delete a transaction (impacts position calculations).

**Endpoint:** `DELETE /api/transactions/{transaction_id}`

**Request:**
```bash
curl -X DELETE http://localhost:8000/api/transactions/789
```

**Response:**
```json
{
  "success": true,
  "message": "Transaction deleted successfully",
  "impact": {
    "positions_affected": ["BTC"],
    "recalculated": true
  }
}
```

---

## Analysis API

### Get Global Market Analysis

Generate AI-powered global market analysis for entire portfolio.

**Endpoint:** `GET /api/analysis/global`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `force_refresh` | boolean | false | Bypass cache and generate new analysis |

**Request:**
```bash
curl "http://localhost:8000/api/analysis/global?force_refresh=false"
```

**Response:**
```json
{
  "analysis": "Market sentiment remains positive with continued strength in tech sector...",
  "market_sentiment": "bullish",
  "key_risks": [
    "Rising interest rates",
    "Geopolitical tensions"
  ],
  "opportunities": [
    "AI sector growth",
    "Crypto market recovery"
  ],
  "generated_at": "2025-11-06T18:00:00",
  "cached": true,
  "tokens_used": 2500
}
```

---

### Get Position Analysis

Generate AI analysis for specific position.

**Endpoint:** `GET /api/analysis/position/{symbol}`

**Request:**
```bash
curl "http://localhost:8000/api/analysis/position/BTC?force_refresh=false"
```

**Response:**
```json
{
  "symbol": "BTC",
  "analysis": "Bitcoin shows strong momentum with recent price increase...",
  "recommendation": "HOLD",
  "confidence": "high",
  "rationale": "Strong fundamentals and positive technical indicators",
  "generated_at": "2025-11-06T18:00:00",
  "cached": true,
  "tokens_used": 1800
}
```

**Recommendation Values:**
- `BUY_MORE` - Add to position
- `HOLD` - Maintain current position
- `TRIM` - Reduce position size
- `SELL` - Exit position

---

### Get Two-Quarter Forecast

Generate price forecast with three scenarios.

**Endpoint:** `GET /api/analysis/forecast/{symbol}`

**Request:**
```bash
curl http://localhost:8000/api/analysis/forecast/BTC
```

**Response:**
```json
{
  "symbol": "BTC",
  "q1": {
    "pessimistic": {
      "price_target": 38000.00,
      "reasoning": "Market correction due to regulatory concerns",
      "confidence": "medium"
    },
    "realistic": {
      "price_target": 45000.00,
      "reasoning": "Continued adoption and positive sentiment",
      "confidence": "high"
    },
    "optimistic": {
      "price_target": 52000.00,
      "reasoning": "ETF approval and institutional adoption",
      "confidence": "medium"
    }
  },
  "q2": {
    "pessimistic": {"price_target": 40000.00, "reasoning": "...", "confidence": "medium"},
    "realistic": {"price_target": 48000.00, "reasoning": "...", "confidence": "high"},
    "optimistic": {"price_target": 58000.00, "reasoning": "...", "confidence": "low"}
  },
  "overall_outlook": "Positive with moderate volatility expected",
  "generated_at": "2025-11-06T18:00:00",
  "tokens_used": 3200
}
```

---

### Bulk Position Analysis

Analyze multiple positions in parallel.

**Endpoint:** `POST /api/analysis/positions/bulk`

**Request:**
```bash
curl -X POST http://localhost:8000/api/analysis/positions/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["BTC", "ETH", "SOL", "AAPL", "MSTR"]
  }'
```

**Response:**
```json
{
  "analyses": {
    "BTC": { "symbol": "BTC", "analysis": "...", "recommendation": "HOLD" },
    "ETH": { "symbol": "ETH", "analysis": "...", "recommendation": "BUY_MORE" },
    "SOL": { "symbol": "SOL", "analysis": "...", "recommendation": "HOLD" }
  },
  "total_tokens_used": 8500
}
```

**Limits:**
- Maximum 10 positions per request
- Performance: ~15-30 seconds for 10 positions

---

## Settings API

### Get All Settings

Get all settings grouped by category.

**Endpoint:** `GET /api/settings`

**Response:**
```json
{
  "categories": [
    {
      "category": "api_keys",
      "display_name": "API Keys",
      "settings": [
        {
          "key": "anthropic_api_key",
          "value": "sk-ant-***",
          "display_name": "Anthropic Claude API Key",
          "is_sensitive": true
        }
      ]
    }
  ]
}
```

---

### Get Settings by Category

Get settings for a specific category.

**Endpoint:** `GET /api/settings/category/{category}`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `reveal` | boolean | false | Show unmasked sensitive values |

**Request:**
```bash
curl "http://localhost:8000/api/settings/category/api_keys?reveal=false"
```

---

### Update Setting

Update a specific setting value.

**Endpoint:** `PUT /api/settings/{setting_key}`

**Request:**
```bash
curl -X PUT http://localhost:8000/api/settings/anthropic_api_key \
  -H "Content-Type: application/json" \
  -d '{
    "value": "sk-ant-api03-new-key-here"
  }'
```

---

## Monitoring API

### Get Market Data Provider Stats

Monitor API usage and rate limits for market data providers.

**Endpoint:** `GET /api/monitoring/market-data`

**Response:**
```json
{
  "yahoo_finance": {
    "enabled": true,
    "total_calls": 1250,
    "successful_calls": 1240,
    "failed_calls": 10,
    "success_rate": 99.2,
    "avg_response_time_ms": 85,
    "cache_hit_rate": 78.5
  },
  "twelve_data": {
    "enabled": true,
    "rate_limits": {
      "calls_per_minute": 8,
      "calls_per_day": 800,
      "current_minute": 3,
      "current_day": 245
    },
    "quota_usage": {
      "daily_percentage": 30.6,
      "approaching_limit": false
    }
  },
  "alpha_vantage": {
    "enabled": true,
    "circuit_breaker": {
      "status": "closed",
      "failure_count": 0,
      "last_failure": null
    }
  }
}
```

---

## Error Codes

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 204 | No Content | Deletion successful |
| 400 | Bad Request | Invalid parameters or request body |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Duplicate resource or conflict |
| 500 | Internal Server Error | Server error during processing |

### Error Response Format

```json
{
  "detail": "Position not found for symbol: INVALID",
  "status_code": 404
}
```

---

## Rate Limits

**Current version:** No rate limits (v1.0)

**Future versions:** Will implement rate limiting per API key

---

## Interactive API Documentation

**Swagger UI:** http://localhost:8000/docs
**ReDoc:** http://localhost:8000/redoc

These provide interactive API exploration and testing.

---

**Need examples?** See [USER-GUIDE.md](./USER-GUIDE.md) for real-world usage scenarios.
