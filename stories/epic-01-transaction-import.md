# Epic 1: Transaction Import & Management

## Epic Overview
**Epic ID**: EPIC-01
**Epic Name**: Transaction Import & Management
**Epic Description**: Enable importing and parsing of Revolut CSV exports with all transaction types
**Business Value**: Automate the manual Excel cleanup process, save hours of manual data entry
**User Impact**: Transform messy Revolut exports into structured, usable transaction data
**Success Metrics**: Successfully parse 100+ transactions, categorize all transaction types correctly
**Status**: 🔴 Not Started

## Features in this Epic
- Feature 1.1: CSV Upload Interface
- Feature 1.2: Revolut CSV Parser
- Feature 1.3: Transaction Storage & Management

## Progress Tracking
| Feature | Stories | Points | Status | Progress |
|---------|---------|--------|--------|----------|
| F1.1: CSV Upload Interface | 2 | 5 | 🔴 Not Started | 0% |
| F1.2: Revolut CSV Parser | 2 | 13 | 🔴 Not Started | 0% |
| F1.3: Transaction Storage | 1 | 5 | 🔴 Not Started | 0% |
| **Total** | **5** | **23** | **Not Started** | **0%** |

---

## Feature 1.1: CSV Upload Interface
**Feature Description**: Web interface for uploading Revolut CSV files
**User Value**: Simple drag-and-drop file upload without command-line tools
**Priority**: High
**Complexity**: 5 story points

### Story F1.1-001: File Upload Component
**Status**: 🔴 Not Started
**User Story**: As FX, I want to upload my Revolut CSV file through a web interface so that I don't need to use command-line tools

**Acceptance Criteria**:
- **Given** I am on the portfolio dashboard
- **When** I click the "Import CSV" button
- **Then** a file picker dialog appears
- **And** I can select only CSV files
- **And** the selected file name is displayed

**Technical Requirements**:
- React component with file input
- File type validation (accept only .csv)
- Max file size: 10MB
- Display selected filename

**Definition of Done**:
- [ ] React component implemented with file input
- [ ] File type validation (CSV only)
- [ ] Upload progress indicator
- [ ] Error handling for invalid files
- [ ] Responsive design for mobile/desktop
- [ ] Unit tests for validation logic
- [ ] Integration test for file upload

**Story Points**: 3
**Priority**: Must Have
**Dependencies**: None
**Risk Level**: Low
**Assigned To**: Unassigned

---

### Story F1.1-002: Upload Status Feedback
**Status**: 🔴 Not Started
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
- [ ] Progress bar component implemented
- [ ] Success/error toast notifications
- [ ] Upload status persists during processing
- [ ] Clear error messages for troubleshooting
- [ ] Retry mechanism for failed uploads
- [ ] Accessibility: ARIA labels for screen readers

**Story Points**: 2
**Priority**: Must Have
**Dependencies**: F1.1-001
**Risk Level**: Low
**Assigned To**: Unassigned

---

## Feature 1.2: Revolut CSV Parser
**Feature Description**: Parse and extract data from Revolut's specific CSV format
**User Value**: Automatically understand and categorize all Revolut transaction types
**Priority**: High
**Complexity**: 13 story points

### Story F1.2-001: Parse Transaction Types
**Status**: 🔴 Not Started
**User Story**: As FX, I want the system to correctly identify all Revolut transaction types so that my portfolio calculations are accurate

**Acceptance Criteria**:
- **Given** a Revolut CSV file with mixed transaction types
- **When** the file is processed
- **Then** BUY transactions are identified as purchases
- **And** SELL transactions are identified as sales
- **And** DIVIDEND transactions are tracked separately
- **And** TOPUP/CARD_PAYMENT transactions are categorized as cash movements
- **And** EXCHANGE transactions are identified as forex
- **And** Unrecognized types are logged with line numbers

**Technical Requirements**:
- Python parser using pandas
- Transaction type enum
- Pattern matching for type identification
- Validation rules for each type
- Comprehensive logging

**Definition of Done**:
- [ ] Parser identifies all transaction types
- [ ] Unit tests for each transaction type
- [ ] Handle edge cases and malformed data
- [ ] Logging for unrecognized transaction types
- [ ] Performance: Parse 10,000 rows in <2 seconds
- [ ] Documentation of supported transaction types

**Story Points**: 5
**Priority**: Must Have
**Dependencies**: F1.1-002
**Risk Level**: Medium
**Assigned To**: Unassigned

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

### Story F1.2-002: Extract Transaction Details
**Status**: 🔴 Not Started
**User Story**: As FX, I want all transaction details extracted accurately so that I can track my investments properly

**Acceptance Criteria**:
- **Given** a parsed Revolut transaction
- **When** extracting transaction details
- **Then** ticker symbol is correctly identified (cleaned of extra text)
- **And** quantity is extracted as decimal number
- **And** price per share is calculated correctly
- **And** transaction date is parsed properly (handles multiple formats)
- **And** currency is identified (USD, EUR, GBP)
- **And** fees are captured if present
- **And** Original CSV row is preserved for audit

**Technical Requirements**:
- Regex patterns for ticker extraction
- Decimal precision for quantities and prices
- Date parsing with multiple format support
- Currency normalization
- Data validation pipeline

**Definition of Done**:
- [ ] All fields extracted with correct data types
- [ ] Date parsing handles multiple formats
- [ ] Currency symbols normalized
- [ ] Ticker symbols cleaned and validated
- [ ] Unit tests with sample Revolut data
- [ ] Handle missing/null values gracefully
- [ ] Performance: Process 1000 transactions/second

**Story Points**: 8
**Priority**: Must Have
**Dependencies**: F1.2-001
**Risk Level**: High
**Assigned To**: Unassigned

**Sample Revolut CSV Format**:
```csv
Date,Time,Type,Product,Ticker,Quantity,Price per share,Total Amount,Currency
2024-10-15,14:30:00,BUY,Tesla Inc,TSLA,10,250.50,2505.00,USD
2024-10-14,10:15:00,DIVIDEND,Apple Inc,AAPL,,0.24,24.00,USD
```

---

## Feature 1.3: Transaction Storage & Management
**Feature Description**: Persist parsed transactions in PostgreSQL with data integrity
**User Value**: Never lose transaction history, enable historical analysis
**Priority**: High
**Complexity**: 5 story points

### Story F1.3-001: Store Transactions in Database
**Status**: 🔴 Not Started
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
    transaction_type VARCHAR(20) NOT NULL,
    ticker VARCHAR(10),
    quantity DECIMAL(18,8),
    price DECIMAL(18,8),
    total_amount DECIMAL(18,8),
    currency VARCHAR(3),
    fee DECIMAL(18,8),
    raw_description TEXT,
    source_file VARCHAR(255),
    import_timestamp TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(transaction_date, ticker, quantity, transaction_type)
);

CREATE INDEX idx_transactions_ticker ON transactions(ticker);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_type ON transactions(transaction_type);
```

**Definition of Done**:
- [ ] Database schema created for transactions
- [ ] SQLAlchemy models implemented
- [ ] Duplicate detection logic with user override option
- [ ] Transaction integrity constraints
- [ ] Database migration scripts
- [ ] Bulk insert optimization (1000+ records)
- [ ] Unit tests for CRUD operations
- [ ] Integration tests with PostgreSQL

**Story Points**: 5
**Priority**: Must Have
**Dependencies**: F1.2-002, F5.2-001 (Database Schema Setup)
**Risk Level**: Medium
**Assigned To**: Unassigned

---

## Technical Design Notes

### CSV Processing Pipeline
```python
1. Upload: File received via FastAPI endpoint
2. Validation: Check file format and size
3. Parsing: Read CSV with pandas
4. Type Detection: Identify transaction types
5. Extraction: Parse details from each row
6. Validation: Verify required fields
7. Storage: Batch insert to PostgreSQL
8. Response: Return success/error summary
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
- **External**: FastAPI file upload, PostgreSQL connection (Epic 5)
- **Internal**: Database schema must exist before storage
- **Libraries**: pandas, SQLAlchemy, python-multipart

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|---------|------------|
| Revolut changes CSV format | Parser breaks | Versioned parsers, format detection |
| Large file uploads timeout | Failed imports | Streaming upload, background processing |
| Duplicate imports | Data corruption | Unique constraints, user confirmation |
| Malformed CSV data | Partial imports | Row-by-row validation, error reporting |

## Testing Strategy
1. **Unit Tests**: Each parser function with mock data
2. **Integration Tests**: Full upload-to-database flow
3. **Performance Tests**: 10,000 transaction file processing
4. **Edge Cases**: Empty files, wrong format, corrupted data
5. **User Acceptance**: Import actual Revolut export file

## Definition of Done for Epic
- [ ] All 5 stories completed
- [ ] Can upload Revolut CSV via web interface
- [ ] All transaction types correctly identified
- [ ] Transaction details accurately extracted
- [ ] Data persisted to PostgreSQL
- [ ] Duplicate imports handled gracefully
- [ ] Performance meets requirements (<5 seconds for 10,000 rows)
- [ ] Error handling comprehensive
- [ ] Unit test coverage >80%
- [ ] Documentation complete