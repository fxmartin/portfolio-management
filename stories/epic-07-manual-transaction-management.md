# Epic 7: Manual Transaction Management

## Epic Overview
**Epic ID**: EPIC-07
**Epic Name**: Manual Transaction Management
**Epic Description**: Enable manual creation, editing, and deletion of transactions to handle edge cases, corrections, and transactions not available via CSV import
**Business Value**: Provide complete transaction management capabilities beyond CSV imports, allowing data corrections and manual entry
**User Impact**: Full control over transaction data with ability to add one-off transactions, fix errors, and manage data not available in exports
**Success Metrics**: Successfully create/edit/delete transactions with automatic position recalculation, maintain data integrity
**Status**: 🔴 Not Started

## Use Cases
1. **Manual Entry**: Add transactions for platforms without CSV export (e.g., private trades, OTC deals)
2. **Data Corrections**: Fix imported transactions with wrong prices, quantities, or dates
3. **Missing Data**: Add staking rewards or airdrops not captured in exports
4. **Adjustments**: Split adjustments, corporate actions, stock dividends
5. **Deletions**: Remove duplicate or erroneous transactions

## Features in this Epic
- Feature 7.1: Manual Transaction Creation
- Feature 7.2: Transaction Editing
- Feature 7.3: Transaction Deletion & Data Integrity
- Feature 7.4: Transaction Validation & Business Rules

## Progress Tracking
| Feature | Stories | Points | Status | Progress |
|---------|---------|--------|--------|----------|
| F7.1: Manual Transaction Creation | 2 | 13 | 🔴 Not Started | 0% (0/13 pts) |
| F7.2: Transaction Editing | 2 | 13 | 🔴 Not Started | 0% (0/13 pts) |
| F7.3: Deletion & Data Integrity | 1 | 8 | 🔴 Not Started | 0% (0/8 pts) |
| F7.4: Validation & Business Rules | 1 | 5 | 🔴 Not Started | 0% (0/5 pts) |
| **Total** | **6** | **39** | **🔴 Not Started** | **0% (0/39 pts)** |

---

## Feature 7.1: Manual Transaction Creation
**Feature Description**: Web form for creating individual transactions manually
**User Value**: Add transactions not available via CSV import or handle one-off trades
**Priority**: High
**Complexity**: 13 story points

### Story F7.1-001: Transaction Input Form
**Status**: 🔴 Not Started
**User Story**: As FX, I want to manually create transactions through a web form so that I can add data not available in CSV exports

**Acceptance Criteria**:
- **Given** I am viewing my transaction list
- **When** I click "Add Transaction"
- **Then** a modal/form appears with all required fields
- **And** I can select transaction type (BUY, SELL, STAKING, AIRDROP, MINING, DEPOSIT, WITHDRAWAL)
- **And** I can enter symbol/ticker with autocomplete
- **And** I can enter quantity, price, fee, and date
- **And** I can select currency (EUR, USD, etc.)
- **And** Form validates all inputs before submission
- **And** I receive confirmation when transaction is saved
- **And** Positions automatically recalculate after creation

**Technical Requirements**:
- React form component with controlled inputs
- Form validation (client-side and server-side)
- Symbol autocomplete using existing positions/tickers
- Date picker with timezone handling
- Currency selector
- Transaction type dropdown with icons
- POST `/api/transactions` endpoint
- Auto-recalculate positions after creation

**Form Fields**:
```typescript
interface TransactionForm {
  transaction_type: 'BUY' | 'SELL' | 'STAKING' | 'AIRDROP' | 'MINING' | 'DEPOSIT' | 'WITHDRAWAL'
  symbol: string           // Required, autocomplete
  quantity: number         // Required, > 0
  price: number           // Required for BUY/SELL, optional for rewards
  fee: number             // Optional, >= 0
  currency: string        // Required, default EUR
  date: DateTime          // Required, not in future
  notes: string           // Optional, max 500 chars
  source: 'MANUAL'        // Auto-set
}
```

**Validation Rules**:
- Quantity must be > 0
- Price must be >= 0 (can be 0 for airdrops)
- Fee must be >= 0
- Date cannot be in the future
- Symbol must exist or be new ticker
- Sell quantity cannot exceed available shares (with warning)
- Required fields: transaction_type, symbol, quantity, currency, date

**Definition of Done**:
- [ ] React form component with all fields
- [ ] Client-side validation with error messages
- [ ] Symbol autocomplete implementation
- [ ] Backend POST endpoint `/api/transactions`
- [ ] Server-side validation
- [ ] Auto-recalculate positions on success
- [ ] Unit tests for validation logic (85% coverage)
- [ ] Integration tests for API endpoint
- [ ] E2E test for complete flow
- [ ] Error handling and user feedback
- [ ] Mobile-responsive design

**Story Points**: 8
**Priority**: Must Have
**Dependencies**: None (uses existing position recalculation)
**Risk Level**: Medium
**Testing Requirements**:
- Unit tests: Form validation, field interactions
- Integration tests: API endpoint, database operations
- E2E tests: Complete transaction creation flow

---

### Story F7.1-002: Bulk Transaction Import
**Status**: 🔴 Not Started
**User Story**: As FX, I want to manually add multiple transactions at once so that I can efficiently enter historical data

**Acceptance Criteria**:
- **Given** I have multiple transactions to add
- **When** I use the bulk import feature
- **Then** I can paste CSV data or use a simplified form
- **And** System validates all transactions before committing
- **And** I see a preview of what will be imported
- **And** I can review and edit before final save
- **And** Batch processing provides progress feedback
- **And** Positions recalculate once after all transactions are saved

**Technical Requirements**:
- Bulk CSV paste interface
- Transaction preview table
- Batch validation
- Progress indicator for large batches
- Transaction-based database operations (rollback on error)
- Single position recalculation after batch

**Definition of Done**:
- [ ] Bulk import UI component
- [ ] CSV parsing for manual input
- [ ] Preview table with edit capability
- [ ] Batch validation endpoint
- [ ] Transaction-based batch creation
- [ ] Progress feedback
- [ ] Unit tests for CSV parsing
- [ ] Integration tests for batch operations
- [ ] Performance test with 100+ transactions

**Story Points**: 5
**Priority**: Should Have
**Dependencies**: F7.1-001
**Risk Level**: Medium

---

## Feature 7.2: Transaction Editing
**Feature Description**: Edit existing transactions to correct errors or update information
**User Value**: Fix mistakes without deleting and recreating transactions
**Priority**: High
**Complexity**: 13 story points

### Story F7.2-001: Edit Transaction Form
**Status**: 🔴 Not Started
**User Story**: As FX, I want to edit existing transactions so that I can correct errors without deleting and recreating them

**Acceptance Criteria**:
- **Given** I am viewing a transaction in the transaction list
- **When** I click "Edit" on a transaction
- **Then** the transaction form opens pre-populated with existing data
- **And** I can modify any editable fields
- **And** System validates changes before saving
- **And** I see a confirmation dialog showing old vs new values
- **And** Positions automatically recalculate after update
- **And** Edit history is logged (audit trail)

**Technical Requirements**:
- Reuse transaction form component from F7.1-001
- PUT `/api/transactions/{id}` endpoint
- Pre-populate form with existing data
- Change confirmation dialog
- Audit log table for transaction changes
- Auto-recalculate positions after update
- Handle edge cases (editing sold positions)

**Audit Trail**:
```typescript
interface TransactionAudit {
  id: number
  transaction_id: number
  changed_at: DateTime
  changed_by: string
  old_values: JSON
  new_values: JSON
  change_reason: string
}
```

**Business Rules**:
- Cannot edit imported transactions' core fields (symbol, quantity, price) - must delete and re-import
- Manual transactions fully editable
- Warn if edit affects closed positions
- Validate that edited SELL doesn't exceed available quantity

**Definition of Done**:
- [ ] Edit form with pre-populated data
- [ ] PUT endpoint for transaction updates
- [ ] Confirmation dialog showing changes
- [ ] Audit trail logging
- [ ] Position recalculation on update
- [ ] Business rule enforcement
- [ ] Unit tests for edit logic (85% coverage)
- [ ] Integration tests for update API
- [ ] E2E test for edit flow
- [ ] Audit log query endpoints

**Story Points**: 8
**Priority**: Must Have
**Dependencies**: F7.1-001
**Risk Level**: Medium
**Testing Requirements**:
- Unit tests: Validation, audit logging
- Integration tests: Update endpoint, position recalculation
- E2E tests: Complete edit flow with confirmation

---

### Story F7.2-002: Transaction History & Audit Log
**Status**: 🔴 Not Started
**User Story**: As FX, I want to see the edit history of transactions so that I can audit changes and maintain data integrity

**Acceptance Criteria**:
- **Given** a transaction has been edited
- **When** I view the transaction details
- **Then** I see a history of all changes
- **And** Each change shows timestamp, old values, new values
- **And** I can compare versions side-by-side
- **And** I can filter audit log by date, user, transaction type

**Technical Requirements**:
- Audit log display component
- GET `/api/transactions/{id}/history` endpoint
- Version comparison UI
- Filterable audit log table

**Definition of Done**:
- [ ] Audit log display component
- [ ] History API endpoint
- [ ] Version comparison view
- [ ] Filter and search functionality
- [ ] Unit tests for history retrieval
- [ ] Integration tests for audit endpoints

**Story Points**: 5
**Priority**: Should Have
**Dependencies**: F7.2-001
**Risk Level**: Low

---

## Feature 7.3: Transaction Deletion & Data Integrity
**Feature Description**: Safely delete transactions with data integrity checks
**User Value**: Remove erroneous or duplicate transactions while maintaining portfolio accuracy
**Priority**: Medium
**Complexity**: 8 story points

### Story F7.3-001: Safe Transaction Deletion
**Status**: 🔴 Not Started
**User Story**: As FX, I want to delete incorrect transactions so that my portfolio data is accurate, with safeguards to prevent data corruption

**Acceptance Criteria**:
- **Given** I have selected a transaction to delete
- **When** I click "Delete"
- **Then** I see a confirmation dialog with impact analysis
- **And** System warns if deletion affects closed positions
- **And** System warns if deletion would create negative holdings
- **And** I can review the impact before confirming
- **And** Positions automatically recalculate after deletion
- **And** Deletion is logged in audit trail
- **And** I can undo deletion within 24 hours (soft delete)

**Technical Requirements**:
- DELETE `/api/transactions/{id}` endpoint
- Impact analysis before deletion
- Soft delete with `deleted_at` timestamp
- Position validation (no negative holdings)
- Auto-recalculate positions
- Undo mechanism (restore soft-deleted)

**Impact Analysis**:
```typescript
interface DeletionImpact {
  transaction_id: number
  affected_positions: string[]  // Symbols affected
  position_changes: {
    symbol: string
    current_quantity: number
    new_quantity: number
    cost_basis_change: number
  }[]
  warnings: string[]  // E.g., "Would create negative holdings"
  can_delete: boolean
}
```

**Business Rules**:
- Soft delete (set `deleted_at`) for 24 hours, then permanent
- Cannot delete if it would create negative holdings
- Warn if deletion affects realized P&L
- Bulk delete requires additional confirmation

**Definition of Done**:
- [ ] DELETE endpoint with soft delete
- [ ] Impact analysis calculation
- [ ] Confirmation dialog with impact preview
- [ ] Position recalculation after delete
- [ ] Undo/restore functionality
- [ ] Permanent deletion after 24 hours (cron job)
- [ ] Unit tests for impact analysis (85% coverage)
- [ ] Integration tests for delete API
- [ ] E2E test for delete flow with undo
- [ ] Audit logging

**Story Points**: 8
**Priority**: Must Have
**Dependencies**: F7.2-001 (audit trail)
**Risk Level**: High
**Testing Requirements**:
- Unit tests: Impact analysis, soft delete logic
- Integration tests: Delete API, position validation
- E2E tests: Delete with confirmation, undo flow

---

## Feature 7.4: Transaction Validation & Business Rules
**Feature Description**: Comprehensive validation and business rules for all transaction operations
**User Value**: Maintain data integrity and prevent invalid portfolio states
**Priority**: High
**Complexity**: 5 story points

### Story F7.4-001: Validation Engine
**Status**: 🔴 Not Started
**User Story**: As FX, I want the system to validate all transaction operations so that my portfolio data remains accurate and consistent

**Acceptance Criteria**:
- **Given** I am creating, editing, or deleting a transaction
- **When** the operation would violate business rules
- **Then** I receive a clear error message
- **And** The system prevents the invalid operation
- **And** I see suggestions to fix the validation error

**Business Rules**:
1. **No Negative Holdings**: Cannot sell more than owned
2. **Valid Dates**: Transaction dates must be chronological for FIFO
3. **Price Validation**: Prices must be reasonable (warn if >50% deviation from market)
4. **Fee Validation**: Fees must be less than transaction value
5. **Currency Consistency**: Warn if mixing currencies for same symbol
6. **Duplicate Detection**: Flag potential duplicates (same symbol, date, quantity)

**Validation Levels**:
- **Error** (blocking): Negative holdings, required fields, invalid dates
- **Warning** (non-blocking): Price deviation, potential duplicates, currency mixing
- **Info**: Suggestions, best practices

**Technical Requirements**:
- Centralized validation service
- Validation rules engine
- Market price lookup for deviation check
- Duplicate detection algorithm
- Clear error messaging

**Validation Service**:
```python
class TransactionValidator:
    def validate_create(self, transaction: Transaction) -> ValidationResult
    def validate_update(self, old: Transaction, new: Transaction) -> ValidationResult
    def validate_delete(self, transaction: Transaction) -> ValidationResult
    def check_holdings(self, symbol: str, date: datetime) -> float
    def detect_duplicates(self, transaction: Transaction) -> List[Transaction]
```

**Definition of Done**:
- [ ] Validation service implementation
- [ ] All business rules implemented
- [ ] Error message catalog
- [ ] Duplicate detection
- [ ] Market price deviation check
- [ ] Unit tests for each validation rule (85% coverage)
- [ ] Integration tests for validation pipeline
- [ ] Documentation of business rules

**Story Points**: 5
**Priority**: Must Have
**Dependencies**: F7.1-001, F7.2-001, F7.3-001
**Risk Level**: Medium
**Testing Requirements**:
- Unit tests: Each validation rule independently
- Integration tests: Validation in create/edit/delete flows
- E2E tests: User-facing error messages

---

## Epic Dependencies

### Internal Dependencies
- Epic 1 (Transaction Import): Shares transaction data model
- Epic 2 (Portfolio Calculation): Uses same FIFO calculator and position recalculation
- Epic 5 (Infrastructure): Database schema supports manual transactions

### External Dependencies
- None

---

## Technical Architecture

### Database Schema Changes
```sql
-- Add to existing transactions table
ALTER TABLE transactions ADD COLUMN source VARCHAR(20) DEFAULT 'CSV';
ALTER TABLE transactions ADD COLUMN notes TEXT;
ALTER TABLE transactions ADD COLUMN deleted_at TIMESTAMP;

-- New audit table
CREATE TABLE transaction_audit (
    id SERIAL PRIMARY KEY,
    transaction_id INTEGER REFERENCES transactions(id),
    changed_at TIMESTAMP DEFAULT NOW(),
    changed_by VARCHAR(100),
    old_values JSONB,
    new_values JSONB,
    change_reason VARCHAR(500)
);

CREATE INDEX idx_audit_transaction ON transaction_audit(transaction_id);
CREATE INDEX idx_audit_date ON transaction_audit(changed_at);
```

### API Endpoints
```
POST   /api/transactions              - Create transaction
GET    /api/transactions              - List all transactions (with filters)
GET    /api/transactions/{id}         - Get transaction details
PUT    /api/transactions/{id}         - Update transaction
DELETE /api/transactions/{id}         - Delete transaction (soft)
POST   /api/transactions/{id}/restore - Restore deleted transaction
GET    /api/transactions/{id}/history - Get audit trail
POST   /api/transactions/bulk         - Bulk create transactions
POST   /api/transactions/validate     - Validate transaction without saving
GET    /api/transactions/duplicates   - Find potential duplicates
```

### Frontend Components
```
components/
  TransactionForm.tsx          - Create/edit form
  TransactionList.tsx          - Transaction table with filters
  TransactionDetails.tsx       - Detail view with history
  BulkImportModal.tsx          - Bulk import interface
  DeletionConfirmDialog.tsx    - Delete confirmation with impact
  AuditLogViewer.tsx          - Transaction history viewer
```

---

## Testing Requirements

### Unit Tests (Target: 85% coverage)
- Form validation logic
- Business rule enforcement
- Impact analysis calculations
- Duplicate detection algorithm
- Audit trail generation

### Integration Tests
- Transaction CRUD operations
- Position recalculation triggers
- Audit logging
- Soft delete and restore
- Bulk operations

### End-to-End Tests
- Complete create/edit/delete flows
- Bulk import workflow
- Undo deletion
- Validation error handling
- Mobile responsiveness

---

## User Experience Considerations

### Mobile Optimization
- Responsive form layouts
- Touch-friendly date pickers
- Simplified bulk import on mobile
- Swipe actions for edit/delete

### Accessibility
- Keyboard navigation for all forms
- Screen reader support (ARIA labels)
- Clear error messaging
- Color-blind friendly validation indicators

### Performance
- Optimistic UI updates
- Debounced validation
- Efficient duplicate detection
- Batch position recalculation

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Data corruption from invalid edits | High | Medium | Comprehensive validation, soft deletes, audit trail |
| Performance with large transaction counts | Medium | Medium | Pagination, indexing, optimized queries |
| FIFO calculation errors after edits | High | Low | Extensive testing, position recalculation verification |
| User confusion about validation rules | Medium | High | Clear error messages, inline help, documentation |
| Duplicate detection false positives | Low | Medium | Configurable thresholds, user override option |

---

## Success Criteria

### MVP Success
- [ ] Create transactions manually with full validation
- [ ] Edit existing transactions with audit trail
- [ ] Delete transactions with impact analysis
- [ ] 85%+ test coverage across all features
- [ ] Position recalculation accuracy maintained (99%+)

### Full Success
- [ ] Bulk import capability
- [ ] Complete audit trail with version comparison
- [ ] Advanced duplicate detection
- [ ] Mobile-optimized experience
- [ ] User documentation complete

---

## Future Enhancements (Post-Epic)
- Import transactions from other platforms (Coinbase, Binance, etc.)
- Transaction templates for recurring entries
- CSV export of transaction list
- Advanced filtering and search
- Transaction tags/categories
- Split transaction support
- Corporate action handling (stock splits, mergers)

---

*Epic created: 2025-10-26*
*Status: Not Started*
*Estimated effort: 39 story points*
