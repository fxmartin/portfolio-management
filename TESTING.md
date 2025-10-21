# Testing Guidelines - Portfolio Management Application

## Core Testing Principles

### ⚠️ MANDATORY REQUIREMENTS
1. **Minimum Coverage Threshold**: 85% code coverage for ALL modules
2. **No story is complete** without passing tests meeting the 85% threshold
3. **Test-Driven Development (TDD)** approach is required:
   - Write tests BEFORE implementation code
   - Only write enough code to make failing tests pass
   - Refactor continuously while keeping tests green

### NO EXCEPTIONS POLICY
Under **no circumstances** should any test type be marked as "not applicable". Every component, regardless of size or complexity, MUST have:
- Unit tests
- Integration tests
- End-to-end tests (where applicable)

## Test Types Required

### 1. Unit Tests (85% minimum coverage)
**Purpose**: Test individual functions and components in isolation

**Required for**:
- All business logic functions
- Data parsers and transformers
- Calculation engines
- React component logic
- Utility functions

**Example areas**:
- CSV parsers (metals, stocks, crypto)
- FIFO calculation algorithms
- Portfolio aggregation functions
- P&L calculations
- Currency conversion logic

### 2. Integration Tests (Mandatory)
**Purpose**: Test component interactions and API endpoints

**Required for**:
- API endpoint functionality
- Database operations (CRUD)
- External API integrations (Yahoo Finance)
- Redis cache operations
- WebSocket connections
- File upload flows

**Example areas**:
- Transaction storage to PostgreSQL
- Price fetching from Yahoo Finance
- Cache read/write to Redis
- Real-time updates via WebSocket

### 3. End-to-End Tests
**Purpose**: Test complete user workflows

**Required for**:
- Critical user paths
- Multi-step processes
- Complex interactions

**Example flows**:
- CSV upload → parsing → storage → display
- Portfolio calculation → visualization
- Live price update → dashboard refresh

## Test Coverage by Epic

### Epic 1: Transaction Import (85% required)
- Unit tests for each CSV parser type
- Integration tests for file upload
- E2E tests for complete import flow

### Epic 2: Portfolio Calculation (85% required)
- Unit tests for FIFO algorithm
- Unit tests for P&L calculations
- Integration tests with database
- Reconciliation tests against Excel

### Epic 3: Live Market Data (85% required)
- Unit tests with mocked API responses
- Integration tests with live API
- Load tests (100+ tickers)
- Failure scenario tests

### Epic 4: Portfolio Visualization (85% required)
- Unit tests for component logic
- Integration tests for API calls
- Visual regression tests
- Performance tests for rendering
- Accessibility tests

### Epic 5: Infrastructure (85% required for code modules)
- Database model tests
- Schema migration tests
- Service integration tests
- Docker configuration validation

## Testing Best Practices

### 1. Test Organization
```
tests/
├── unit/
│   ├── parsers/
│   ├── calculations/
│   └── components/
├── integration/
│   ├── api/
│   ├── database/
│   └── external/
└── e2e/
    └── workflows/
```

### 2. Test Naming Conventions
- Use descriptive names that explain what is being tested
- Format: `test_<function>_<scenario>_<expected_result>`
- Example: `test_fifo_calculator_with_multiple_sells_returns_correct_cost_basis`

### 3. Test Data
- Use realistic test data that mirrors production
- Maintain test fixtures for each CSV format type
- Create edge case datasets (empty, malformed, extreme values)

### 4. Mocking Strategy
- Mock external dependencies (APIs, databases) in unit tests
- Use real connections in integration tests
- Maintain mock data consistency across tests

### 5. Performance Testing
- Transaction processing: <5 seconds for 10,000 rows
- Price fetching: <2 seconds for 50 tickers
- Dashboard load: <2 seconds initial load
- Chart rendering: <500ms for 1000 data points

## Definition of Done Checklist

A story is **NOT complete** until:

- [ ] Unit tests written and passing (≥85% coverage)
- [ ] Integration tests written and passing
- [ ] E2E tests written for critical paths
- [ ] All tests run in CI/CD pipeline
- [ ] No test failures or skipped tests
- [ ] Test coverage report generated and reviewed
- [ ] Edge cases and error scenarios tested
- [ ] Performance benchmarks met
- [ ] Documentation updated with test examples

## Testing Tools and Frameworks

### Backend (Python)
- **Unit Testing**: pytest
- **Coverage**: pytest-cov
- **Mocking**: pytest-mock, unittest.mock
- **Integration**: pytest + FastAPI test client
- **Database**: pytest-postgresql

### Frontend (React/TypeScript)
- **Unit Testing**: Jest + React Testing Library
- **Component Testing**: Storybook
- **E2E Testing**: Cypress or Playwright
- **Coverage**: Jest coverage reports

### Infrastructure
- **Docker Testing**: docker-compose test configurations
- **Database Migrations**: Alembic tests

## Coverage Reporting

### Generating Coverage Reports
```bash
# Backend
pytest --cov=backend --cov-report=html --cov-report=term

# Frontend
npm test -- --coverage --watchAll=false
```

### Coverage Requirements
- Minimum: 85% overall coverage
- Critical paths: 95% coverage
- New code: 90% coverage minimum

## Continuous Integration

### CI Pipeline Requirements
1. Run all tests on every commit
2. Block merge if coverage < 85%
3. Generate coverage badges
4. Store test reports as artifacts
5. Run tests in parallel when possible

### Test Execution Order
1. Linting and formatting checks
2. Unit tests
3. Integration tests
4. E2E tests (on main branches)
5. Coverage report generation

## Common Testing Scenarios

### CSV Parser Testing
```python
def test_revolut_metals_parser_valid_file():
    # Given a valid metals CSV file
    # When parsed
    # Then all transactions extracted correctly
    # And asset_type is 'METAL'
```

### FIFO Calculation Testing
```python
def test_fifo_multiple_buys_single_sell():
    # Given multiple buy transactions
    # When a partial sell occurs
    # Then correct lots are consumed
    # And cost basis is accurate
```

### API Endpoint Testing
```python
def test_upload_csv_endpoint():
    # Given a valid CSV file
    # When uploaded via API
    # Then returns 200 status
    # And transactions stored in database
```

## Troubleshooting

### Common Issues
1. **Flaky tests**: Use proper waits, avoid time-dependent logic
2. **Database state**: Reset database between tests
3. **External API calls**: Mock in unit tests, use test accounts in integration
4. **Race conditions**: Proper async/await handling

### Debug Tips
- Run tests in verbose mode for detailed output
- Use debugger breakpoints in failing tests
- Check test isolation (run individual tests)
- Verify test data consistency

## Review Checklist

Before submitting code for review:
- [ ] All new code has corresponding tests
- [ ] Tests follow naming conventions
- [ ] Coverage meets 85% threshold
- [ ] Tests are deterministic (not flaky)
- [ ] Test data is realistic
- [ ] Edge cases are covered
- [ ] Performance tests pass benchmarks
- [ ] Documentation includes test examples

---

Remember: **A story without tests is an incomplete story.** Testing is not optional - it's a fundamental part of our development process that ensures quality, reliability, and maintainability.