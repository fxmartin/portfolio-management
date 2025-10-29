# Epic 8: AI-Powered Market Analysis

**NOTE**: This epic has been split into multiple files for better manageability.

📋 **[Start Here: Epic Overview](./epic-08-overview.md)** - Executive summary, progress tracking, architecture

---

## Feature Documentation

This epic contains 14 stories across 6 features (67 story points total):

### 🗂️ [Feature 8.1: Prompt Management System](./epic-08-f1-prompt-management.md)
**Complexity**: 13 points | **Stories**: 3 | **Status**: ✅ Complete (Oct 29, 2025)

Database-backed system for storing, editing, and versioning analysis prompts.

**Stories**:
- F8.1-001: Database Schema for Prompts (5 pts) ✅
- F8.1-002: Prompt CRUD API (5 pts) ✅
- F8.1-003: Prompt Template Engine (3 pts) ✅

**Tests**: 103 passing (18 schema + 25 service + 21 API + 39 renderer), 98% coverage

---

### 🤖 [Feature 8.2: Anthropic Claude Integration](./epic-08-f2-claude-integration.md)
**Complexity**: 13 points | **Stories**: 2 | **Status**: 🔴 Not Started

Core integration with Anthropic Claude API for generating market analysis.

**Stories**:
- F8.2-001: Claude API Client (8 pts)
- F8.2-002: Analysis Service Layer (5 pts)

---

### 🌍 [Feature 8.3: Global Market Analysis](./epic-08-f3-global-analysis.md)
**Complexity**: 8 points | **Stories**: 2 | **Status**: 🔴 Not Started

Portfolio-wide market analysis providing overall market sentiment and macro insights.

**Stories**:
- F8.3-001: Global Analysis API (3 pts)
- F8.3-002: Market Context Data Collection (5 pts)

---

### 📊 [Feature 8.4: Position-Level Analysis](./epic-08-f4-position-analysis.md)
**Complexity**: 10 points | **Stories**: 2 | **Status**: 🔴 Not Started

AI analysis for individual positions with specific recommendations (HOLD/BUY/SELL).

**Stories**:
- F8.4-001: Position Analysis API (5 pts)
- F8.4-002: Position Context Enhancement (5 pts)

---

### 🔮 [Feature 8.5: Forecasting Engine with Scenarios](./epic-08-f5-forecasting.md)
**Complexity**: 15 points | **Stories**: 3 | **Status**: 🔴 Not Started

Generate two-quarter forecasts with pessimistic, realistic, and optimistic scenarios.

**Stories**:
- F8.5-001: Forecast API (8 pts)
- F8.5-002: Forecast Data Collection (5 pts)
- F8.5-003: Forecast Accuracy Tracking (5 pts)

---

### 💻 [Feature 8.6: Analysis UI Dashboard](./epic-08-f6-analysis-ui.md)
**Complexity**: 8 points | **Stories**: 2 | **Status**: 🔴 Not Started

Frontend components for displaying and interacting with AI analysis.

**Stories**:
- F8.6-001: Analysis Dashboard Tab (5 pts)
- F8.6-002: Forecast Visualization (5 pts)

---

## Quick Links

- 📋 [Epic Overview](./epic-08-overview.md) - Start here for executive summary
- 🗂️ [Feature 8.1: Prompts](./epic-08-f1-prompt-management.md)
- 🤖 [Feature 8.2: Claude](./epic-08-f2-claude-integration.md)
- 🌍 [Feature 8.3: Global Analysis](./epic-08-f3-global-analysis.md)
- 📊 [Feature 8.4: Position Analysis](./epic-08-f4-position-analysis.md)
- 🔮 [Feature 8.5: Forecasting](./epic-08-f5-forecasting.md)
- 💻 [Feature 8.6: Analysis UI](./epic-08-f6-analysis-ui.md)

---

## Development Notes

**Original file archived**: `epic-08-ai-market-analysis.md.backup` (90KB)

**Split completed**: Oct 29, 2025
- Original file: 2,748 lines, 90KB
- Split into: 1 overview + 6 feature files
- Total stories: 14 (67 points)

This organization makes it easier to:
- Navigate and find specific stories
- Track progress per feature
- Review and update documentation
- Avoid overwhelming file sizes
