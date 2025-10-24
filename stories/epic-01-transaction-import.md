# Epic 1: Transaction Import & Management

## Epic Overview
**Epic ID**: EPIC-01
**Epic Name**: Transaction Import & Management
**Epic Description**: Enable importing and parsing of three specific CSV formats: Revolut metals (account-statement), Revolut stocks, and Koinly crypto transactions
**Business Value**: Automate the import of metals, stocks, and crypto transactions from different sources
**User Impact**: Seamlessly import transactions from Revolut (metals & stocks) and Koinly (crypto) exports
**Success Metrics**: Successfully parse all three CSV formats, correctly categorize metals/stocks/crypto transactions
**Status**: ✅ Complete (Started: 2025-10-21, Completed: 2025-10-21)

## CSV File Specifications

### 1. Metals Transactions (Revolut Account Statement)
- **Filename Pattern**: `account-statement_YYYY-MM-DD_YYYY-MM-DD_en_XXXXXX.csv`
- **Example**: `account-statement_2025-06-15_2025-10-21_en_4cab86.csv`
- **Source**: Revolut App → Statements → Export
- **Content**: Gold, Silver, and other precious metals transactions

### 2. Stocks Transactions (Revolut Export)
- **Filename Pattern**: `[UUID].csv`
- **Example**: `B5A12617-2B56-4A79-B83D-13C6715DC0BA.csv`
- **Source**: Revolut App → Stocks → Export
- **Content**: Stock buy/sell transactions, dividends

### 3. Crypto Transactions (Koinly Export)
- **Filename**: `Koinly Transactions.csv`
- **Source**: Koinly App (synced with Revolut crypto account)
- **Content**: Cryptocurrency transactions for tax reporting
- **Note**: Koinly provides enhanced tax-ready format with cost basis calculations

## Features in this Epic
- Feature 1.1: Multi-Format CSV Upload Interface
- Feature 1.2: Three-Parser System (Metals, Stocks, Crypto)
- Feature 1.3: Transaction Storage & Management (including Database Statistics)

## Progress Tracking
| Feature | Stories | Points | Status | Progress |
|---------|---------|--------|--------|----------|
| F1.1: Multi-Format CSV Upload | 2 | 5 | ✅ Complete | 100% (5/5 pts) |
| F1.2: Three-Parser System | 3 | 18 | ✅ Complete | 100% (18/18 pts) |
| F1.3: Storage & DB Management | 3 | 11 | ✅ Complete | 100% (11/11 pts) |
| **Total** | **8** | **31** | ✅ **Complete** | **100% (31/31 pts)** |

---

## Feature 1.1: Multi-Format CSV Upload Interface
**Feature Description**: Web interface for uploading three different CSV formats (metals, stocks, crypto)
**User Value**: Single interface to import all transaction types with automatic format detection
**Priority**: High
**Complexity**: 5 story points

### Story F1.1-001: Multi-File Upload Component
**Status**: ✅ Complete (2025-10-21)
**User Story**: As FX, I want to upload my metals, stocks, and crypto CSV files through a web interface with automatic format detection

**Acceptance Criteria**:
- **Given** I am on the portfolio dashboard
- **When** I click the "Import Transactions" button
- **Then** a file picker dialog appears
- **And** I can select one or multiple CSV files
- **And** the system auto-detects the file type based on filename pattern
- **And** file types are displayed (Metals/Stocks/Crypto)
- **And** I can review files before processing

**Technical Requirements**:
- React component with multi-file input
- File type detection logic:
  - `account-statement_*` → Metals
  - UUID pattern → Stocks
  - `Koinly*` → Crypto
- Support for drag-and-drop
- Max file size: 10MB per file
- Display file list with type badges

**Definition of Done**:
- [x] React component implemented with file input
- [x] File type validation (CSV only)
- [x] Upload progress indicator
- [x] Error handling for invalid files
- [x] Responsive design for mobile/desktop
- [x] Unit tests for validation logic (21 tests passing)
- [x] Integration test for file upload (15 tests passing)

**Story Points**: 3
**Priority**: Must Have
**Dependencies**: None
**Risk Level**: Low
**Assigned To**: Completed
**Implementation Date**: 2025-10-21

**Implementation Notes**:
- Created `TransactionImport.tsx` component with full drag-and-drop support
- Implemented `csv_parser.py` module for file type detection
- Added `/api/import/upload` endpoint supporting multiple files
- Color-coded badges: 🟡 METALS, 🟢 STOCKS, 🟣 CRYPTO
- All 36 backend tests passing
- All 17 frontend tests passing

---

### Story F1.1-002: Upload Status Feedback
**Status**: ✅ Complete (2025-10-21)
**User Story**: As FX, I want to see the upload progress and status so that I know if my file was processed successfully

**Acceptance Criteria**:
- **Given** I have selected a CSV file to upload
- **When** I click "Upload"
- **Then** I see a progress bar showing upload status
- **And** I receive a success message when complete
- **And** I see an error message if upload fails
- **And** Error messages are specific and actionable

**Technical Requirements**:
- Progress bar component
- Toast notifications for success/error
- Axios interceptors for upload progress
- Error message mapping

**Definition of Done**:
- [x] Progress bar component implemented
- [x] Success/error toast notifications
- [x] Upload status persists during processing
- [x] Clear error messages for troubleshooting
- [x] Retry mechanism for failed uploads
- [x] Accessibility: ARIA labels for screen readers

**Story Points**: 2
**Priority**: Must Have
**Dependencies**: F1.1-001
**Risk Level**: Low
**Assigned To**: Completed
**Implementation Date**: 2025-10-21

**Implementation Notes**:
- Created `Toast.tsx` component with success, error, warning, and info types
- Implemented `ProgressBar.tsx` with determinate and indeterminate modes
- Added `useToast.ts` custom hook for toast management
- Created `errorMessages.ts` utility for user-friendly error mapping
- Enhanced TransactionImport component with full progress tracking
- Added retry mechanism with up to 2 retry attempts
- Full ARIA labels and keyboard navigation support
- 62 unit and integration tests passing
- Resolved ESM module import issues by co-locating types in Toast component

---

## Feature 1.2: Three-Parser System
**Feature Description**: Parse and extract data from three different CSV formats (metals, stocks, crypto)
**User Value**: Automatically parse different formats and normalize data for unified processing
**Priority**: High
**Complexity**: 15 story points

### Story F1.2-001: Parse Metals Transactions (Revolut Account Statement)
**Status**: ✅ Complete (2025-10-21)
**User Story**: As FX, I want the system to parse my Revolut metals account statement so I can track my precious metals investments

**Acceptance Criteria**:
- **Given** an account-statement CSV file from Revolut
- **When** the file is processed
- **Then** metals BUY transactions are identified (Gold, Silver, etc.) ✅
- **And** metals SELL transactions are captured ✅
- **And** metal type is extracted (XAU for Gold, XAG for Silver) ✅
- **And** quantity is in troy ounces ✅
- **And** prices are per troy ounce ✅
- **And** currency conversions are handled ✅
- **And** fees are captured if present ✅

**Technical Requirements**:
- Python parser using csv module ✅
- Transaction type enum ✅
- Pattern matching for type identification ✅
- Validation rules for each type ✅
- Comprehensive logging (deferred to future story)

**Definition of Done**:
- [x] Parser identifies all transaction types (BUY/SELL based on amount sign)
- [x] Unit tests for each transaction type (14 comprehensive tests)
- [x] Handle edge cases and malformed data
- [ ] Logging for unrecognized transaction types (deferred)
- [x] Performance: Parse 10,000 rows in <2 seconds
- [x] Documentation of supported transaction types

**Story Points**: 5
**Priority**: Must Have
**Dependencies**: F1.1-002
**Risk Level**: Medium
**Assigned To**: Completed

**Implementation Notes**:
```python
# Expected transaction types from Revolut
TRANSACTION_TYPES = {
    'BUY': 'purchase',
    'SELL': 'sale',
    'DIVIDEND': 'dividend',
    'TOPUP': 'cash_in',
    'CARD_PAYMENT': 'cash_out',
    'EXCHANGE': 'forex',
    'CUSTODY_FEE': 'fee'
}
```

---

### Story F1.2-002: Parse Stocks Transactions (Revolut UUID Export)
**Status**: ✅ Complete (2025-10-21)
**User Story**: As FX, I want the system to parse my Revolut stocks export so I can track my stock investments and dividends

**Acceptance Criteria**:
- **Given** a UUID-named CSV file from Revolut stocks export
- **When** the file is processed
- **Then** stock BUY transactions are identified
- **And** stock SELL transactions are captured
- **And** DIVIDEND transactions are tracked
- **And** ticker symbols are extracted (e.g., AAPL, TSLA)
- **And** fractional shares are handled
- **And** price per share is captured
- **And** transaction dates and times are parsed
- **And** currency is identified (typically USD)

**Technical Requirements**:
- Regex patterns for ticker extraction
- Decimal precision for quantities and prices
- Date parsing with multiple format support
- Currency normalization
- Data validation pipeline

**Definition of Done**:
- [x] All fields extracted with correct data types
- [x] Date parsing handles multiple formats
- [x] Currency symbols normalized
- [x] Ticker symbols cleaned and validated
- [x] Unit tests with sample Revolut data (16 comprehensive tests)
- [x] Handle missing/null values gracefully (dividends without quantity)
- [x] Performance: Process 1000 transactions/second

**Story Points**: 8
**Priority**: Must Have
**Dependencies**: F1.2-001
**Risk Level**: High
**Assigned To**: Completed
**Implementation Date**: 2025-10-21

**Implementation Notes**:
- Implemented `StocksParser` class in `csv_parser.py`
- Handles BUY, SELL, and DIVIDEND transaction types
- Supports fractional shares
- Properly handles missing quantity for dividend transactions
- Preserves raw CSV data for audit purposes
- Includes FX rate handling for multi-currency support
- 16 comprehensive unit tests with 94% code coverage
- Integration tests updated and passing
- **Bug Fix (Issue #11, 2025-10-24)**: Added thousands separator handling - parser now strips commas from large amounts before float conversion to prevent ValueError on transactions like "$5,000"

**Expected Revolut Stocks CSV Format**:
```csv
Date,Time,Type,Product,Ticker,Quantity,Price per share,Total Amount,Currency,FX Rate
2024-10-15,14:30:00,BUY,Tesla Inc,TSLA,10,250.50,2505.00,USD,1.0
2024-10-14,10:15:00,DIVIDEND,Apple Inc,AAPL,,0.24,24.00,USD,1.0
```

---

### Story F1.2-003: Parse Crypto Transactions (Koinly Export)
**Status**: ✅ Complete (2025-10-21)
**User Story**: As FX, I want the system to parse my Koinly crypto export so I can track my cryptocurrency investments with tax calculations

**Acceptance Criteria**:
- **Given** a Koinly Transactions.csv file
- **When** the file is processed
- **Then** crypto BUY transactions are identified
- **And** crypto SELL transactions are captured
- **And** STAKING rewards are tracked
- **And** crypto symbols are extracted (BTC, ETH, etc.)
- **And** cost basis from Koinly is preserved
- **And** tax lot information is captured
- **And** transaction fees in crypto or fiat are handled
- **And** USD equivalent values are captured

**Technical Requirements**:
- Koinly-specific CSV format parser
- Tax lot tracking
- Cost basis preservation
- Multiple currency handling

**Expected Koinly CSV Format**:
```csv
Date,Type,In Amount,In Currency,Out Amount,Out Currency,Fee Amount,Fee Currency,Net Value(USD),Label,Description,TxHash
2024-01-15,Buy,0.5,BTC,25000,USD,10,USD,24990,,,0x123...
2024-02-20,Staking,0.001,ETH,,,,,2.50,reward,,0x456...
```

**Definition of Done**:
- [x] Parser identifies Koinly format
- [x] All transaction types parsed (BUY, SELL, STAKING, AIRDROP, MINING, DEPOSIT, WITHDRAWAL, EXCHANGE)
- [x] Cost basis preserved from Koinly
- [x] Tax lot information maintained
- [x] Unit tests with sample Koinly data (19 comprehensive tests)
- [x] Handle Koinly-specific fields

**Story Points**: 5
**Priority**: Must Have
**Dependencies**: F1.1-001
**Risk Level**: Medium
**Assigned To**: Completed
**Implementation Date**: 2025-10-21

**Implementation Notes**:
- Implemented `CryptoParser` class in `csv_parser.py`
- Handles all major Koinly transaction types
- Added new transaction types to models: AIRDROP, MINING, DEPOSIT, WITHDRAWAL
- Properly parses crypto-to-crypto swaps as two transactions (SELL + BUY)
- Preserves transaction hash, labels, and cost basis from Koinly
- Skips pure fiat transactions (USD deposits/withdrawals)
- 19 comprehensive unit tests with 100% pass rate
- Handles decimal precision for fractional crypto amounts
- Preserves raw CSV data for audit trail

---

## Feature 1.3: Transaction Storage & Database Management
**Feature Description**: Persist parsed transactions in PostgreSQL with data integrity, provide database reset capability, and display comprehensive statistics
**User Value**: Reliable transaction storage with visibility into imported data and ability to start fresh when needed
**Priority**: High
**Complexity**: 8 story points

### Story F1.3-001: Store Transactions in Database
**Status**: ✅ Complete (2025-10-21)
**User Story**: As FX, I want all my transactions stored persistently so that I don't need to re-import my CSV files

**Acceptance Criteria**:
- **Given** parsed transaction data
- **When** saving to database
- **Then** all transaction fields are stored correctly
- **And** duplicate imports are detected and prevented (based on date+ticker+quantity)
- **And** source file name is tracked for audit trail
- **And** import timestamp is recorded
- **And** User can choose to override duplicates
- **And** Database transaction ensures all-or-nothing import

**Technical Requirements**:
- SQLAlchemy models for transactions
- Unique constraint for duplicate detection
- Batch insert for performance
- Transaction rollback on error
- Import metadata tracking

**Database Schema**:
```sql
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    transaction_date TIMESTAMP NOT NULL,
    asset_type VARCHAR(10) NOT NULL, -- 'METAL', 'STOCK', 'CRYPTO'
    transaction_type VARCHAR(20) NOT NULL, -- 'BUY', 'SELL', 'DIVIDEND', 'STAKING'
    symbol VARCHAR(20) NOT NULL, -- 'XAU', 'AAPL', 'BTC', etc.
    quantity DECIMAL(18,8),
    price_per_unit DECIMAL(18,8),
    total_amount DECIMAL(18,8),
    currency VARCHAR(3),
    fee DECIMAL(18,8),
    cost_basis DECIMAL(18,8), -- From Koinly for crypto
    tax_lot_id VARCHAR(100), -- For tax tracking
    raw_data JSONB, -- Original CSV row for audit
    source_file VARCHAR(255),
    source_type VARCHAR(10), -- 'REVOLUT', 'KOINLY'
    import_timestamp TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(transaction_date, symbol, quantity, transaction_type, asset_type)
);

CREATE INDEX idx_transactions_symbol ON transactions(symbol);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_type ON transactions(transaction_type);
CREATE INDEX idx_transactions_asset_type ON transactions(asset_type);
CREATE INDEX idx_transactions_source ON transactions(source_file);
```

**Definition of Done**:
- [x] Database schema created for transactions ✅
- [x] SQLAlchemy models implemented ✅
- [x] Duplicate detection logic with user override option ✅
- [x] Transaction integrity constraints ✅
- [x] Database migration scripts ✅
- [x] Bulk insert optimization (1000+ records) ✅
- [x] Unit tests for CRUD operations ✅
- [x] Integration tests with PostgreSQL ✅

**Story Points**: 5
**Priority**: Must Have
**Dependencies**: F1.2-002, F5.2-001 (Database Schema Setup)
**Risk Level**: Medium
**Assigned To**: Completed
**Implementation Date**: 2025-10-21

**Implementation Notes**:
- Created `TransactionService` class for database operations
- Implemented duplicate detection based on unique constraint
- Added support for three duplicate strategies: skip, update, force
- Created `/api/import/upload` endpoint with batch processing
- Added `/api/import/summary` for transaction statistics
- Added `/api/import/check-duplicates` for pre-import validation
- Comprehensive error handling with detailed per-transaction feedback
- 12 unit tests for transaction service (100% pass rate)
- Integration tests for complete import flow
- Tested with real Revolut metals CSV - successfully stored 3 transactions

---

### Story F1.3-002: Database Reset Functionality
**Status**: ✅ Complete (2025-10-21)
**User Story**: As FX, I want to reset the database and clear all transactions so that I can start fresh with clean imports or fix import mistakes

**Acceptance Criteria**:
- **Given** I have transactions in the database
- **When** I trigger the reset function
- **Then** a confirmation dialog appears with warning
- **And** I must confirm the action (type "DELETE ALL" or similar)
- **And** all transactions are deleted from the database
- **And** all positions are cleared
- **And** all price history is cleared
- **And** all portfolio snapshots are removed
- **And** import metadata is reset
- **And** a success message confirms the reset
- **And** an audit log entry is created with timestamp

**Technical Requirements**:
- API endpoint for database reset
- Frontend confirmation modal
- Database transaction for atomic deletion
- Cascade delete for related tables
- Audit logging for reset operations

**Safety Features**:
```python
class DatabaseResetService:
    def reset_database(self, confirmation_code: str):
        # Require explicit confirmation
        if confirmation_code != "DELETE_ALL_TRANSACTIONS":
            raise ValueError("Invalid confirmation code")

        # Log the reset operation
        self.log_reset_operation()

        # Perform atomic deletion
        with db.begin():
            db.execute("TRUNCATE TABLE transactions CASCADE")
            db.execute("TRUNCATE TABLE positions CASCADE")
            db.execute("TRUNCATE TABLE price_history CASCADE")
            db.execute("TRUNCATE TABLE portfolio_snapshots CASCADE")

        return {"status": "success", "message": "Database reset complete"}
```

**API Endpoint**:
```python
@app.post("/api/database/reset")
async def reset_database(
    confirmation: str = Body(...),
    current_user: User = Depends(get_current_user)
):
    if confirmation != "DELETE_ALL_TRANSACTIONS":
        raise HTTPException(status_code=400, detail="Invalid confirmation")

    # Create audit log
    audit_log.info(f"Database reset initiated by {current_user.id}")

    # Perform reset
    result = DatabaseResetService().reset_database(confirmation)

    return result
```

**Frontend Component**:
```typescript
const DatabaseResetModal: React.FC = () => {
  const [confirmText, setConfirmText] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);

  const handleReset = async () => {
    if (confirmText !== 'DELETE ALL TRANSACTIONS') {
      alert('Please type exactly: DELETE ALL TRANSACTIONS');
      return;
    }

    if (!window.confirm('This will permanently delete ALL transactions. Are you absolutely sure?')) {
      return;
    }

    setIsDeleting(true);
    try {
      await axios.post('/api/database/reset', {
        confirmation: 'DELETE_ALL_TRANSACTIONS'
      });
      window.location.reload(); // Refresh to show empty state
    } catch (error) {
      alert('Reset failed: ' + error.message);
    }
    setIsDeleting(false);
  };

  return (
    <Modal>
      <h2>⚠️ Dangerous Operation</h2>
      <p>This will permanently delete:</p>
      <ul>
        <li>All imported transactions</li>
        <li>All manually entered transactions</li>
        <li>All position calculations</li>
        <li>All price history</li>
        <li>All portfolio snapshots</li>
      </ul>
      <p>Type <code>DELETE ALL TRANSACTIONS</code> to confirm:</p>
      <input
        type="text"
        value={confirmText}
        onChange={(e) => setConfirmText(e.target.value)}
        placeholder="Type confirmation here"
      />
      <button
        onClick={handleReset}
        disabled={isDeleting || confirmText !== 'DELETE ALL TRANSACTIONS'}
        className="danger-button"
      >
        {isDeleting ? 'Deleting...' : 'Reset Database'}
      </button>
    </Modal>
  );
};
```

**Definition of Done**:
- [x] API endpoint for database reset implemented
- [x] Confirmation mechanism requires exact text
- [x] Frontend modal with warnings
- [x] All tables cleared (transactions, positions, history, snapshots)
- [x] Atomic transaction ensures all-or-nothing
- [x] Audit log captures reset operations
- [x] Unit tests for reset logic (12 tests)
- [x] Integration tests for API endpoints (10 tests)
- [x] Frontend component tests (17 tests)
- [x] Documentation includes warnings

**Story Points**: 3
**Priority**: Should Have
**Dependencies**: F1.3-001
**Risk Level**: High (Destructive operation)
**Assigned To**: Completed
**Implementation Date**: 2025-10-21

**Implementation Notes**:
- Created `DatabaseResetService` class with atomic transaction handling
- Implemented `/api/database/reset` endpoint with confirmation validation
- Added `/api/database/stats` endpoint for current database metrics
- Added `/api/database/health` endpoint for connection testing
- Created `DatabaseResetModal` React component with multi-step confirmation
- Requires exact text "DELETE_ALL_TRANSACTIONS" for confirmation
- Tables deleted in correct order to respect foreign key constraints
- Primary key sequences reset to 1 after deletion
- Comprehensive audit logging of all reset operations
- 39 total tests written (22 backend, 17 frontend) with 100% pass rate
- Modal automatically clears state when closed/reopened
- Progress indication during deletion process
- Page automatically reloads after successful reset

---

### Story F1.3-003: Database Statistics Dashboard
**Status**: ✅ Complete
**User Story**: As FX, I want to see database statistics at a glance so that I can understand how much data has been imported and monitor the system's state

**Acceptance Criteria**:
- **Given** I am on the portfolio dashboard
- **When** I click the "Database Stats" button
- **Then** I see a modal or panel showing:
  - Total number of transactions
  - Breakdown by asset type (Metals, Stocks, Crypto)
  - Breakdown by transaction type (BUY, SELL, DIVIDEND, etc.)
  - Date range of transactions (earliest to latest)
  - Number of unique symbols/assets
  - Total records across all tables
  - Database connection health status
- **And** Statistics update in real-time when new imports occur
- **And** I can refresh the statistics manually
- **And** Numbers are formatted for readability (e.g., 1,234)

**Technical Requirements**:
- React component for statistics display
- Use existing `/api/database/stats` endpoint
- Add `/api/import/summary` integration for detailed breakdown
- Card-based layout with icons for each metric
- Auto-refresh every 30 seconds (optional toggle)
- Loading states during data fetch
- Error handling for failed API calls

**UI/UX Design**:
```typescript
interface DatabaseStats {
  transactions: {
    total: number;
    byAssetType: Record<string, number>;
    byTransactionType: Record<string, number>;
    dateRange: { earliest: string; latest: string };
  };
  symbols: {
    total: number;
    topSymbols: Array<{ symbol: string; count: number }>;
  };
  database: {
    tablesCount: Record<string, number>;
    totalRecords: number;
    isHealthy: boolean;
    lastImport?: string;
  };
}
```

**Component Structure**:
```tsx
<DatabaseStatsModal>
  <StatsHeader>
    <Title>Database Statistics</Title>
    <RefreshButton onClick={handleRefresh} />
    <AutoRefreshToggle checked={autoRefresh} />
  </StatsHeader>

  <StatsGrid>
    <StatCard icon="📊" title="Total Transactions">
      {formatNumber(stats.transactions.total)}
    </StatCard>

    <StatCard icon="📈" title="Asset Types">
      <PieChart data={stats.transactions.byAssetType} />
    </StatCard>

    <StatCard icon="📅" title="Date Range">
      {formatDateRange(stats.transactions.dateRange)}
    </StatCard>

    <StatCard icon="💼" title="Unique Assets">
      {stats.symbols.total} symbols
    </StatCard>

    <StatCard icon="🗄️" title="Database Health">
      <HealthIndicator status={stats.database.isHealthy} />
    </StatCard>
  </StatsGrid>

  <DetailsSection>
    <TransactionBreakdown data={stats.transactions.byTransactionType} />
    <TopSymbolsList symbols={stats.symbols.topSymbols} />
  </DetailsSection>
</DatabaseStatsModal>
```

**Definition of Done**:
- [x] React component created with modal/panel display
- [x] Integration with `/api/database/stats/detailed` endpoint
- [x] Card-based responsive layout
- [x] Number formatting utilities
- [x] Auto-refresh functionality with toggle
- [x] Loading and error states
- [x] Unit tests for component logic (17 tests)
- [x] Unit tests for backend (8 tests)
- [x] Accessibility: keyboard navigation and ARIA labels
- [x] Mobile-responsive design

**Story Points**: 3
**Priority**: Should Have
**Dependencies**: F1.3-001 (Database storage must be working)
**Risk Level**: Low
**Assigned To**: Completed
**Implementation Date**: 2025-10-21

**Implementation Notes**:
- Created `/api/database/stats/detailed` endpoint with comprehensive breakdown
- Enhanced `DatabaseResetService.get_detailed_stats()` method
- Created `DatabaseStats` React component with card-based layout
- Displays breakdown by asset type, transaction type, top symbols
- Shows date ranges, unique symbol count, and database health
- Auto-refresh toggle with configurable interval (default: 30s)
- Number formatting with thousand separators
- Icons for visual clarity (🏆 Metals, 📈 Stocks, ₿ Crypto)
- Responsive CSS Grid layout for mobile/desktop
- 25 total tests written (8 backend, 17 frontend) with 100% pass rate
- Graceful error handling and fallback UI states
- Modal overlay pattern for better UX

---

## Technical Design Notes

### Multi-Format CSV Processing Pipeline
```python
1. Upload: Multiple files received via FastAPI endpoint
2. Format Detection: Identify file type (Metals/Stocks/Crypto)
3. Parser Selection: Route to appropriate parser
4. Parsing: Read CSV with pandas using format-specific logic
5. Normalization: Convert to unified transaction format
6. Validation: Verify required fields per format
7. Storage: Batch insert to PostgreSQL with asset_type field
8. Response: Return summary per file type
```

### File Type Detection Logic
```python
def detect_csv_type(filename: str) -> str:
    if filename.startswith('account-statement_'):
        return 'METALS'
    elif re.match(r'^[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}\.csv$', filename, re.I):
        return 'STOCKS'
    elif 'koinly' in filename.lower():
        return 'CRYPTO'
    else:
        raise ValueError(f"Unknown CSV format: {filename}")
```

### Unified Transaction Model
```python
class UnifiedTransaction:
    date: datetime
    asset_type: str  # 'METAL', 'STOCK', 'CRYPTO'
    transaction_type: str  # 'BUY', 'SELL', 'DIVIDEND', 'STAKING'
    symbol: str  # 'XAU', 'AAPL', 'BTC'
    quantity: Decimal
    price_per_unit: Decimal
    total_amount: Decimal
    currency: str
    fee: Decimal
    source_file: str
    raw_data: dict  # Original row data for audit
```

### Error Handling Strategy
- Invalid file format: Return specific error message
- Parsing errors: Log row number and continue
- Database errors: Rollback transaction and retry
- Duplicate detection: Offer user choice to skip or update

### Performance Considerations
- Streaming parse for large files (>10MB)
- Batch database inserts (1000 records at a time)
- Background processing for files >1000 rows
- Progress updates via WebSocket or SSE

---

## Dependencies
- **External**: FastAPI file upload, ~~PostgreSQL connection (Epic 5)~~ ✅ COMPLETE
- **Internal**: ~~Database schema must exist before storage~~ ✅ COMPLETE (F5.2-001)
- **Libraries**: pandas, SQLAlchemy, python-multipart

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|---------|------------|
| Revolut changes CSV format | Parser breaks | Versioned parsers, format detection |
| Large file uploads timeout | Failed imports | Streaming upload, background processing |
| Duplicate imports | Data corruption | Unique constraints, user confirmation |
| Malformed CSV data | Partial imports | Row-by-row validation, error reporting |

## Testing Strategy

**⚠️ MANDATORY TESTING REQUIREMENT**:
- **Minimum Coverage Threshold**: 85% code coverage for all modules
- **No story is complete without passing tests meeting this threshold**

1. **Unit Tests** (Required - 85% minimum coverage): Each parser function with mock data
   - Metals parser with account-statement format
   - Stocks parser with UUID format
   - Crypto parser with Koinly format
2. **Integration Tests** (Required): Full upload-to-database flow
   - Multi-file upload handling
   - Format detection accuracy
3. **Performance Tests**:
   - 10,000 transaction file processing
   - Multiple large files simultaneously
4. **Edge Cases**:
   - Empty files, wrong format, corrupted data
   - Mixed file types in single upload
   - Duplicate detection across file types
5. **User Acceptance**:
   - Import actual Revolut metals export
   - Import actual Revolut stocks export
   - Import actual Koinly crypto export

## Definition of Done for Epic
- [ ] All 7 stories completed (3/7 complete)
- [x] Can upload multiple CSV files via web interface ✅
- [x] Auto-detection of file types (Metals/Stocks/Crypto) ✅
- [x] Upload progress feedback with progress bars ✅
- [x] Toast notifications for success/error/warning messages ✅
- [x] Retry mechanism for failed uploads ✅
- [ ] Three parsers working correctly:
  - [x] Metals parser handles account-statement format ✅
  - [x] Stocks parser handles UUID format ✅
  - [ ] Crypto parser handles Koinly format
- [ ] All transaction types correctly identified per format
- [ ] Data normalized to unified transaction model
- [ ] Data persisted to PostgreSQL with asset_type field
- [ ] Database reset functionality with safety confirmations
- [ ] Duplicate imports handled gracefully
- [ ] Performance meets requirements (<5 seconds for 10,000 rows)
- [x] Error handling comprehensive (for upload component with user-friendly messages) ✅
- [x] Unit test coverage ≥85% (mandatory threshold) - Upload and feedback component tests complete ✅
- [ ] Documentation complete with sample files