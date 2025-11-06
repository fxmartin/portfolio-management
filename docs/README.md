# Portfolio Management Documentation

This directory contains comprehensive documentation for the Portfolio Management application.

## 📚 Documentation Index

### User Documentation (Start Here!)

#### [QUICK-START.md](./QUICK-START.md) - Get Running in 5 Minutes ⚡
**Installation & First Steps**

Get your portfolio tracker up and running quickly:
- **Prerequisites**: Docker, Docker Compose, CSV files
- **Installation Steps**: Clone, configure, start (3 steps)
- **First Actions**: Import transactions, view portfolio
- **Quick Commands**: Essential commands reference
- **Common Issues**: Port conflicts, connection problems

**When to read**: First time setup, getting started quickly

---

#### [USER-GUIDE.md](./USER-GUIDE.md) - Complete Feature Walkthrough 📖
**How to Use the Application**

Complete user guide covering all features:
- **Dashboard Overview**: Portfolio summary, positions, P&L, charts
- **Importing Transactions**: CSV formats, multi-file uploads, duplicates
- **Managing Transactions**: Create, edit, delete, audit trail
- **Portfolio Tracking**: FIFO calculations, fees, multi-currency
- **AI-Powered Analysis**: Global analysis, position insights, forecasts
- **Rebalancing**: Target allocations, recommendations, alignment score
- **Investment Strategy**: Define strategy, get AI-driven recommendations
- **Settings**: Configure API keys, preferences, prompts

**When to read**: Learning features, daily usage, exploring capabilities

---

#### [CSV-IMPORT-GUIDE.md](./CSV-IMPORT-GUIDE.md) - CSV Import Reference 📄
**Complete CSV Format Documentation**

Deep dive on all supported CSV formats:
- **Revolut Metals**: Format, columns, transaction detection
- **Revolut Stocks**: Format, columns, dividend handling
- **Koinly Crypto**: Format, columns, staking/airdrops
- **File Naming**: Detection rules, renaming guide
- **Import Process**: Step-by-step workflow
- **Troubleshooting**: Common errors, validation tips

**When to read**: Preparing CSV exports, troubleshooting imports, understanding formats

---

#### [API-REFERENCE.md](./API-REFERENCE.md) - REST API Documentation 🔌
**Complete Endpoint Reference**

Full API documentation with examples:
- **Import API**: Upload CSVs, check duplicates
- **Portfolio API**: Summary, positions, prices, history
- **Transactions API**: CRUD operations, bulk import
- **Analysis API**: Global analysis, position analysis, forecasts
- **Rebalancing API**: Generate recommendations
- **Strategy API**: Define strategy, get recommendations
- **Settings API**: Manage configuration
- **Monitoring API**: Provider stats, rate limits
- **Error Codes**: HTTP status codes, error format

**When to read**: Integrating with API, automation, understanding endpoints

---

#### [CONFIGURATION.md](./CONFIGURATION.md) - Configuration Guide ⚙️
**Environment & Settings Reference**

Complete configuration documentation:
- **Environment Variables**: Database, API keys, encryption
- **Application Settings**: Currency, format, performance
- **Market Data**: Provider configuration, rate limits
- **Performance Tuning**: Cache optimization, resource limits
- **Docker Configuration**: Ports, volumes, resource limits
- **Security**: Credential rotation, best practices

**When to read**: Initial setup, adding API keys, performance tuning

---

#### [COMMAND-REFERENCE.md](./COMMAND-REFERENCE.md) - Command Guide 💻
**All Available Commands**

Complete command reference:
- **Makefile Commands**: dev, test, logs, clean, backup
- **Docker Commands**: Container management, logs, exec
- **Backend Commands**: Package management, testing, migrations
- **Frontend Commands**: npm scripts, testing, linting
- **Database Commands**: SQL queries, maintenance
- **Git Workflow**: Conventional commits, branching

**When to read**: Daily development, troubleshooting, learning workflows

---

#### [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Problem Solving 🔧
**Common Problems & Solutions**

User-friendly troubleshooting guide:
- **Installation Problems**: Docker, permissions, dependencies
- **Service Startup**: Port conflicts, container crashes
- **Database Issues**: Connection, authentication, performance
- **Import Errors**: File detection, columns, duplicates
- **Price Data**: Updates, rate limits, symbols
- **Performance**: Slow loading, memory, caching
- **API Errors**: 500, 404, 400, timeouts
- **Frontend Issues**: White screen, CORS, hot reload
- **Recovery Procedures**: Reset, backup, restore

**When to read**: Solving problems, debugging errors, recovering from failures

---

### Technical Documentation (Developers)

#### [AI_ANALYSIS.md](./AI_ANALYSIS.md) - AI-Powered Market Analysis System
**Epic 8 Complete Guide** (1,000+ lines)

Complete technical documentation for the AI market analysis system powered by Anthropic Claude:
- **Prompt Templates** (3 types): Global analysis, position recommendations, two-quarter forecasts
- **Data Collection**: 10-18 fields collected from portfolio and market APIs
- **Claude API Integration**: Rate limiting, retry logic, token tracking
- **Response Processing**: JSON extraction, recommendation parsing, validation
- **Caching Strategy**: Redis caching with 1-24 hour TTLs (75% hit rate)
- **Database Storage**: 3 tables (prompts, versions, results) with audit trail
- **Cost Tracking**: ~$4.50/month with caching optimization
- **Testing**: 181 tests passing (100% coverage)

**When to read**: Understanding AI analysis features, customizing prompts, debugging Claude API calls, estimating costs

---

#### [ARCHITECTURE.md](./ARCHITECTURE.md) - System Design & Technical Architecture
**System Overview & Design Patterns**

High-level architectural documentation:
- **Service Communication Flows**: React → FastAPI → PostgreSQL/Redis
- **Database Schema**: Tables, relationships, indexes
- **Component Design Patterns**: Factory, Router, Service layer patterns
- **Technology Stack**: Python 3.12, FastAPI, React 18, PostgreSQL, Redis
- **CSV Processing Pipeline**: Detection → Parsing → Validation → Storage
- **FIFO Calculator**: Cost basis calculations with fee handling

**When to read**: Understanding system design, onboarding new developers, planning new features

---

#### [SECURITY.md](./SECURITY.md) - Security Best Practices
**Credential Management & Security Guidelines**

Security documentation covering:
- **Environment Variable Management**: `.env` file structure and `.env.example` template
- **API Key Storage**: Anthropic Claude, Alpha Vantage, database credentials
- **Database Security**: Connection strings, user permissions
- **Secret Handling**: Never commit secrets, use environment variables
- **Rotation Procedures**: How to rotate API keys and database passwords
- **GitIgnore Configuration**: Ensuring sensitive files are excluded

**When to read**: Initial setup, rotating credentials, security audits, adding new API integrations

---

#### [TESTING.md](./TESTING.md) - Testing Strategy & Requirements
**85% Coverage Threshold & TDD Approach**

Testing requirements and best practices:
- **Minimum Coverage Threshold**: 85% code coverage (mandatory)
- **Test Types**: Unit tests, integration tests, end-to-end tests
- **TDD Approach**: Write tests before implementation
- **Running Tests**: Backend (pytest), Frontend (Vitest)
- **Test Suite Status**: 676/676 backend tests passing (100%), 351/372 frontend tests (94.4%)
- **Coverage Reporting**: pytest-cov for backend, Vitest coverage for frontend
- **Definition of Done**: No story complete without passing tests at 85% threshold

**When to read**: Writing new features, debugging test failures, understanding coverage requirements

---

#### [DEBUGGING.md](./DEBUGGING.md) - Comprehensive Debugging Guide
**VS Code, Docker & Database Debugging**

Debugging tools and troubleshooting:
- **VS Code Debugging**: 4 launch configurations (backend attach/test, frontend Chrome/Edge)
- **Docker Debugging**: Container inspection, logs, shell access
- **Database Debugging**: PostgreSQL connection, query debugging, pgAdmin
- **Common Issues**: Port conflicts, volume permissions, dependency issues
- **Troubleshooting Flowcharts**: Step-by-step problem resolution
- **Makefile Commands**: 30+ developer helper commands

**When to read**: Setting up development environment, debugging issues, learning Docker workflows

---

## 📖 Additional Resources

### Project Documentation (Root Directory)

- **[../CLAUDE.md](../CLAUDE.md)** - Development guidance for AI assistants
  - Essential commands and workflows
  - Architecture overview
  - Critical implementation notes
  - Testing requirements
  - Environment variables

- **[../STORIES.md](../STORIES.md)** - Story overview and progress tracking
  - 9 epics, 69 stories, 316 story points
  - 83% complete (261/316 points)
  - Recent updates and completed features
  - Test infrastructure status

- **[../PRD.md](../PRD.md)** - Product Requirements Document
  - Product vision and goals
  - User personas
  - Feature specifications
  - Success metrics

### Epic Definitions (../stories/ Directory)

Detailed story breakdowns for each epic:
- **Epic 1**: Transaction Import & Management (31 pts) ✅
- **Epic 2**: Portfolio Calculation Engine (26 pts) ✅
- **Epic 3**: Live Market Data Integration (16 pts) ✅
- **Epic 4**: Portfolio Visualization (63 pts) 🟡 84%
- **Epic 5**: Infrastructure & DevOps (13 pts) ✅
- **Epic 6**: UI Modernization & Navigation (18 pts) ✅
- **Epic 7**: Manual Transaction Management (39 pts) ✅
- **Epic 8**: AI-Powered Market Analysis (70 pts) 🟡 93%
- **Epic 9**: Settings Management (50 pts) 🔴 Not Started

---

## 🚀 Quick Navigation

### For New Users (First Time Setup)
1. Start with [QUICK-START.md](./QUICK-START.md) - Get running in 5 minutes
2. Read [USER-GUIDE.md](./USER-GUIDE.md) - Learn all features
3. Check [CSV-IMPORT-GUIDE.md](./CSV-IMPORT-GUIDE.md) - Import your transactions
4. Review [CONFIGURATION.md](./CONFIGURATION.md) - Set up API keys

### For Daily Usage
1. [USER-GUIDE.md](./USER-GUIDE.md) - Feature reference
2. [COMMAND-REFERENCE.md](./COMMAND-REFERENCE.md) - All commands
3. [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Solve problems
4. [API-REFERENCE.md](./API-REFERENCE.md) - API integration

### For New Developers
1. Start with [QUICK-START.md](./QUICK-START.md) for environment setup
2. Read [ARCHITECTURE.md](./ARCHITECTURE.md) for system overview
3. Check [TESTING.md](./TESTING.MD) for testing requirements
4. Review [SECURITY.md](./SECURITY.md) for credential setup

### For Feature Development
1. Check [../STORIES.md](../STORIES.md) for current sprint focus
2. Read relevant epic file in `../stories/` for acceptance criteria
3. Review [TESTING.md](./TESTING.md) for testing requirements
4. Follow TDD approach: tests first, then implementation

### For AI Analysis Features
1. Read [AI_ANALYSIS.md](./AI_ANALYSIS.md) for complete system documentation
2. Check `backend/seed_prompts.py` for default prompt templates
3. Review `backend/prompt_renderer.py` for data collection logic
4. See `backend/analysis_service.py` for orchestration flow

### For Troubleshooting
1. Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for user-level problems
2. Check [DEBUGGING.md](./DEBUGGING.md) for developer-level debugging
3. Review logs: `make logs` or `docker-compose logs -f`
4. Inspect database: `make shell-db` or pgAdmin (localhost:5050)
5. Check test failures: `make test` for detailed output

---

## 📝 Documentation Standards

All documentation in this directory follows these standards:

### Structure
- **Overview section** - Purpose and scope
- **Table of contents** - Navigation for long documents
- **Code examples** - Real implementation snippets
- **Command examples** - Copy-paste ready commands
- **Troubleshooting** - Common issues and solutions

### Markdown Conventions
- Headers use ATX style (`#`, `##`, `###`)
- Code blocks specify language for syntax highlighting
- Links use relative paths (e.g., `./AI_ANALYSIS.md`)
- File paths use backticks (e.g., `` `backend/main.py` ``)
- Commands use code blocks with bash syntax

### Maintenance
- Update documentation when features change
- Version documentation with "Last Updated" dates
- Keep examples current with actual implementation
- Cross-reference related documentation

---

## 🔄 Recent Updates

### October 29, 2025
- **Created**: `AI_ANALYSIS.md` - Complete Epic 8 documentation (1,000+ lines)
- **Organized**: Moved all core documentation to `docs/` directory
- **Updated**: README.md with comprehensive documentation index

### October 28, 2025
- **Updated**: `DEBUGGING.md` - Added VS Code debugging configurations
- **Updated**: `TESTING.md` - Test infrastructure overhaul status

### October 27, 2025
- **Created**: `SECURITY.md` - Credential management guide

---

## 📊 Documentation Metrics

| Document | Lines | Status | Last Updated |
|----------|-------|--------|--------------|
| AI_ANALYSIS.md | 1,000+ | ✅ Complete | Oct 29, 2025 |
| ARCHITECTURE.md | 500+ | ✅ Complete | Oct 21, 2025 |
| DEBUGGING.md | 350+ | ✅ Complete | Oct 28, 2025 |
| SECURITY.md | 200+ | ✅ Complete | Oct 27, 2025 |
| TESTING.md | 200+ | ✅ Complete | Oct 21, 2025 |

**Total Documentation**: ~2,250 lines across 5 core documents

---

## 📧 Contributing to Documentation

When adding or updating documentation:

1. **Follow existing structure**: Match the style of existing docs
2. **Include code examples**: Show real implementation snippets
3. **Add troubleshooting**: Document common issues you encounter
4. **Update this README**: Add new documents to the index
5. **Cross-reference**: Link related documentation
6. **Version control**: Note "Last Updated" dates

---

**Last Updated**: October 29, 2025
**Documentation Version**: 1.0
