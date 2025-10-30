# Epic 8: AI-Powered Market Analysis

## Epic Overview
**Epic ID**: EPIC-08
**Epic Name**: AI-Powered Market Analysis with Claude
**Epic Description**: Integrate Anthropic Claude API to provide intelligent market analysis, forecasts, and insights aligned with portfolio positions
**Business Value**: Transform raw portfolio data into actionable insights and predictive forecasts for better investment decisions
**User Impact**: Receive AI-powered analysis of market conditions, position-specific insights, and two-quarter forecasts with confidence levels

**Success Metrics**:
- Analysis generation time <10 seconds for global analysis
- Position analysis <5 seconds per asset
- Forecast accuracy tracking >60% for realistic scenarios
- User engagement: Analysis viewed within 5 minutes of generation

**Status**: 🟡 IN PROGRESS - 70% Complete (70/101 pts, F8.7 & F8.8 pending)

## Features in this Epic
- [Feature 8.1: Prompt Management System](./epic-08-f1-prompt-management.md) ✅ (13 points, 3 stories) - COMPLETE
- [Feature 8.2: Anthropic Claude Integration](./epic-08-f2-claude-integration.md) ✅ (13 points, 2 stories) - COMPLETE
- [Feature 8.3: Global Market Analysis](./epic-08-f3-global-analysis.md) ✅ (8 points, 2 stories) - COMPLETE
- [Feature 8.4: Position-Level Analysis](./epic-08-f4-position-analysis.md) ✅ (15 points, 3 stories) - COMPLETE
- [Feature 8.5: Forecasting Engine with Scenarios](./epic-08-f5-forecasting.md) ✅ (13 points, 2 stories) - COMPLETE
- [Feature 8.6: Analysis UI Dashboard](./epic-08-f6-analysis-ui.md) ✅ (8 points, 3 stories) - COMPLETE
- [Feature 8.7: AI-Powered Portfolio Rebalancing](./epic-08-f7-rebalancing.md) 🔴 (18 points, 3 stories) - NOT STARTED
- [Feature 8.8: Strategy-Driven Portfolio Allocation](./epic-08-f8-strategy-driven-allocation.md) 🔴 (13 points, 3 stories) - NOT STARTED

## Progress Tracking
| Feature | Stories | Points | Status | Progress | File |
|---------|---------|--------|--------|----------|------|
| F8.1: Prompt Management | 3 | 13 | ✅ Complete | 100% (13/13 pts) | [Details](./epic-08-f1-prompt-management.md) |
| F8.2: Claude Integration | 2 | 13 | ✅ Complete | 100% (13/13 pts) | [Details](./epic-08-f2-claude-integration.md) |
| F8.3: Global Analysis | 2 | 8 | ✅ Complete | 100% (8/8 pts) | [Details](./epic-08-f3-global-analysis.md) |
| F8.4: Position Analysis | 3 | 15 | ✅ Complete | 100% (15/15 pts) | [Details](./epic-08-f4-position-analysis.md) |
| F8.5: Forecasting Engine | 2 | 13 | ✅ Complete | 100% (13/13 pts) | [Details](./epic-08-f5-forecasting.md) |
| F8.6: Analysis UI | 3 | 8 | ✅ Complete | 100% (8/8 pts) | [Details](./epic-08-f6-analysis-ui.md) |
| F8.7: Portfolio Rebalancing | 3 | 18 | 🔴 Not Started | 0% (0/18 pts) | [Details](./epic-08-f7-rebalancing.md) |
| F8.8: Strategy-Driven Allocation | 3 | 13 | 🔴 Not Started | 0% (0/13 pts) | [Details](./epic-08-f8-strategy-driven-allocation.md) |
| **Total** | **21** | **101** | **🟡 IN PROGRESS** | **70% (70/101 pts)** | |

---

## Technical Architecture Overview

```
┌─────────────┐
│   React UI  │
│  (Analysis  │
│   Dashboard)│
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────────┐
│  FastAPI        │
│  /api/analysis/ │
└──────┬──────────┘
       │
       ├──► PromptService ──► PostgreSQL (prompts table)
       │
       ├──► AnalysisService
       │      │
       │      ├──► PromptRenderer (template engine)
       │      ├──► DataCollector (portfolio/market data)
       │      └──► ClaudeService ──► Anthropic API
       │
       └──► CacheService ──► Redis (1h TTL for analysis, 24h for forecasts)
```

## Data Flow
1. **User requests analysis** → Frontend calls `/api/analysis/{type}/{symbol?}`
2. **Check cache** → Redis lookup with key `analysis:{type}:{symbol}`
3. **If cache miss**:
   - Fetch prompt template from database
   - Collect portfolio/market data
   - Render template with data
   - Call Claude API
   - Parse and validate response
   - Store in database (`analysis_results` table)
   - Cache in Redis
4. **Return to user** → Markdown analysis or structured forecast

## Token Budget Estimate
- **Anthropic Tier 1**: 50 req/min, ~4M tokens/day
- **Typical usage**:
  - Global analysis: ~1,500 tokens
  - Position analysis: ~800 tokens
  - Forecast: ~2,000 tokens
- **Daily estimate** (10 positions, 2 analyses/day each):
  - 1 global × 1,500 = 1,500
  - 10 positions × 800 × 2 = 16,000
  - 5 forecasts × 2,000 = 10,000
  - **Total**: ~27,500 tokens/day (well within limits)

## Dependencies
- **External**:
  - Anthropic Claude API (anthropic Python SDK ≥0.18.0)
  - Portfolio positions (Epic 2)
  - Yahoo Finance data (Epic 3)
- **Internal**:
  - Database schema must exist before prompts
  - Claude client must work before analysis service
  - Analysis service must work before UI

## Risks & Mitigations
| Risk | Impact | Likelihood | Mitigation |
|------|--------|----------|------------|
| Anthropic API changes | Analysis breaks | Low | Abstract API layer, version pinning |
| Token costs exceed budget | High costs | Medium | Aggressive caching, usage monitoring |
| Claude hallucinations | Bad advice | Medium | Disclaimer in UI, forecast accuracy tracking |
| JSON parsing failures | Forecast errors | Low | Robust parsing with fallbacks |
| Rate limiting | Service degradation | Low | Queue system, rate limiter |

## Testing Requirements

**⚠️ MANDATORY TESTING REQUIREMENT**:
- **Minimum Coverage Threshold**: 85% code coverage for all modules
- **No story is complete without passing tests meeting this threshold**

1. **Unit Tests** (Required - 85% minimum):
   - Prompt rendering engine
   - Claude API client (mocked)
   - Analysis service logic
   - Forecast parsing
   - Data collection

2. **Integration Tests** (Required):
   - End-to-end prompt → Claude → response flow
   - Database storage and retrieval
   - Cache integration

3. **Performance Tests**:
   - Analysis generation time (<10s global, <5s position, <15s forecast)
   - Concurrent request handling
   - Cache hit ratio validation

## Performance Requirements
- **Global analysis**: <10 seconds fresh, <100ms cached
- **Position analysis**: <5 seconds fresh, <100ms cached
- **Forecast**: <15 seconds fresh, <100ms cached
- **Bulk operations**: Linear scaling (5 positions = 5× single time)
- **Cache hit ratio**: >70% during normal usage

## Security Considerations
- **API Key**: Stored in environment variables only, never in code/DB
- **Rate Limiting**: Prevent abuse with per-user rate limits
- **Input Validation**: Sanitize all user inputs before rendering
- **Template Injection**: Use safe template substitution
- **CORS**: Restrict API access to frontend origin

## Definition of Done for Epic
- [ ] All 21 stories completed (14/21 complete - 67%, F8.4-003, F8.6-003, F8.7 & F8.8 pending)
- [x] Database schema for prompts and analysis results ✅
- [x] Anthropic Claude integration working ✅
- [x] Global, position, and forecast analysis functional ✅
- [x] Frontend UI for viewing all analysis types ✅
- [x] Caching system reducing API costs ✅ (Redis integration complete)
- [ ] Forecast accuracy tracking implemented (Future enhancement)
- [x] Unit test coverage ≥85% (mandatory) ✅ (676/676 tests passing, 100% pass rate)
- [x] Integration tests passing ✅
- [x] API documentation complete ✅
- [x] Performance benchmarks met ✅ (<10s global, <5s position, <15s forecast)
- [ ] **F8.4-003: Portfolio context integration** (5 pts - adds strategic recommendations based on full portfolio composition)
- [ ] **F8.6-003: Indicator Tooltips Enhancement** (3 pts - adds explanatory tooltips for all 19 market indicators)
- [ ] **F8.7: AI-Powered Portfolio Rebalancing** (18 pts):
  - [ ] F8.7-001: Rebalancing Analysis Engine (8 pts)
  - [ ] F8.7-002: Claude-Powered Rebalancing Recommendations (5 pts)
  - [ ] F8.7-003: Rebalancing UI Dashboard (5 pts)
- [ ] **F8.8: Strategy-Driven Portfolio Allocation** (13 pts - NEW FEATURE):
  - [ ] F8.8-001: Investment Strategy Storage & API (5 pts)
  - [ ] F8.8-002: Claude Strategy-Driven Recommendations (5 pts)
  - [ ] F8.8-003: Strategy Management UI (3 pts)

---

## Future Enhancements (Post-MVP)
1. **News Integration**: Pull relevant news for context
2. **Sentiment Analysis**: Analyze market sentiment from social media
3. **Custom Prompts**: Let users create their own analysis prompts
4. **Scheduled Analysis**: Automatically run analysis daily/weekly
5. **Email Alerts**: Send analysis updates via email
6. **PDF Reports**: Export analysis as PDF for record-keeping
7. **Multi-Model Support**: Compare forecasts from different LLMs
8. **Historical Analysis Archive**: Browse past analyses
9. **Voice Analysis**: Generate audio summaries with TTS
10. **Collaborative Notes**: Add personal notes to analyses
