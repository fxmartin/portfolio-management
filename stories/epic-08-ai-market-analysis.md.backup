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
**Status**: 🔴 Not Started

## Features in this Epic
- Feature 8.1: Prompt Management System 🔴
- Feature 8.2: Anthropic Claude Integration 🔴
- Feature 8.3: Global Market Analysis 🔴
- Feature 8.4: Position-Level Analysis 🔴
- Feature 8.5: Forecasting Engine with Scenarios 🔴
- Feature 8.6: Analysis UI Dashboard 🔴

## Progress Tracking
| Feature | Stories | Points | Status | Progress |
|---------|---------|--------|--------|----------|
| F8.1: Prompt Management | 3 | 13 | 🔴 Not Started | 0% (0/13 pts) |
| F8.2: Claude Integration | 2 | 13 | 🔴 Not Started | 0% (13 pts) |
| F8.3: Global Analysis | 2 | 8 | 🔴 Not Started | 0% (0/8 pts) |
| F8.4: Position Analysis | 2 | 10 | 🔴 Not Started | 0% (0/10 pts) |
| F8.5: Forecasting Engine | 3 | 15 | 🔴 Not Started | 0% (0/15 pts) |
| F8.6: Analysis UI | 2 | 8 | 🔴 Not Started | 0% (0/8 pts) |
| **Total** | **14** | **67** | **🔴 Not Started** | **0% (0/67 pts)** |

---

## Feature 8.1: Prompt Management System
**Feature Description**: Database-backed system for storing, editing, and versioning analysis prompts
**User Value**: Customize and refine analysis prompts over time without code changes
**Priority**: High (Foundation for all analysis features)
**Complexity**: 13 story points

### Story F8.1-001: Database Schema for Prompts
**Status**: 🔴 Not Started
**User Story**: As FX, I want prompts stored in the database so that I can manage and version them without touching code

**Acceptance Criteria**:
- **Given** the need for flexible prompt management
- **When** the system initializes
- **Then** a `prompts` table exists with proper schema
- **And** a `prompt_versions` table tracks historical changes
- **And** default prompts are seeded on first run
- **And** prompts support template variables (e.g., {portfolio_value}, {positions})

**Database Schema**:
```sql
CREATE TABLE prompts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50) NOT NULL,  -- 'global', 'position', 'forecast'
    prompt_text TEXT NOT NULL,
    template_variables JSONB,  -- {portfolio_value: "decimal", positions: "array"}
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    version INTEGER DEFAULT 1
);

CREATE TABLE prompt_versions (
    id SERIAL PRIMARY KEY,
    prompt_id INTEGER REFERENCES prompts(id),
    version INTEGER NOT NULL,
    prompt_text TEXT NOT NULL,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP DEFAULT NOW(),
    change_reason TEXT
);

CREATE TABLE analysis_results (
    id SERIAL PRIMARY KEY,
    analysis_type VARCHAR(50) NOT NULL,  -- 'global', 'position', 'forecast'
    symbol VARCHAR(20),  -- NULL for global analysis
    prompt_id INTEGER REFERENCES prompts(id),
    prompt_version INTEGER,
    raw_response TEXT NOT NULL,
    parsed_data JSONB,  -- Structured analysis data
    tokens_used INTEGER,
    generation_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP  -- For caching/cleanup
);

CREATE INDEX idx_analysis_type_symbol ON analysis_results(analysis_type, symbol);
CREATE INDEX idx_analysis_created_at ON analysis_results(created_at DESC);
```

**Default Prompts Seed Data**:
```python
DEFAULT_PROMPTS = [
    {
        "name": "global_market_analysis",
        "category": "global",
        "prompt_text": """You are a professional financial analyst providing market insights for a portfolio management application.

Current Portfolio Context:
- Total Value: {portfolio_value}
- Asset Allocation: {asset_allocation}
- Open Positions: {position_count}
- Top Holdings: {top_holdings}

Provide a succinct market analysis (200-300 words) covering:
1. Current market sentiment and key trends
2. Macro-economic factors affecting this portfolio
3. Sector-specific insights relevant to holdings
4. Risk factors to monitor

Be direct, data-driven, and actionable. Focus on what matters for this specific portfolio mix.""",
        "template_variables": {
            "portfolio_value": "decimal",
            "asset_allocation": "object",
            "position_count": "integer",
            "top_holdings": "array"
        }
    },
    {
        "name": "position_analysis",
        "category": "position",
        "prompt_text": """Analyze the following investment position for a personal portfolio:

Asset: {symbol} ({name})
Current Holdings: {quantity} shares/units
Current Price: {current_price}
Cost Basis: {cost_basis}
Unrealized P&L: {unrealized_pnl} ({pnl_percentage}%)
Position Size: {position_percentage}% of portfolio

Market Context:
- 24h Change: {day_change}%
- Sector: {sector}
- Asset Type: {asset_type}

Provide analysis (150-200 words) covering:
1. Current market position and recent performance
2. Key factors driving price movement
3. Risk assessment for this holding
4. Recommended action: HOLD, BUY_MORE, REDUCE, or SELL (with brief rationale)

Be concise and actionable.""",
        "template_variables": {
            "symbol": "string",
            "name": "string",
            "quantity": "decimal",
            "current_price": "decimal",
            "cost_basis": "decimal",
            "unrealized_pnl": "decimal",
            "pnl_percentage": "decimal",
            "position_percentage": "decimal",
            "day_change": "decimal",
            "sector": "string",
            "asset_type": "string"
        }
    },
    {
        "name": "forecast_two_quarters",
        "category": "forecast",
        "prompt_text": """Generate a two-quarter price forecast for the following asset:

Asset: {symbol} ({name})
Current Price: {current_price}
52-Week Range: {week_52_low} - {week_52_high}
Recent Performance: {performance_30d} (30d), {performance_90d} (90d)
Sector: {sector}
Asset Type: {asset_type}

Market Context:
{market_context}

Provide a structured forecast for Q1 and Q2 (next 6 months) with:
1. **Pessimistic Scenario**: Conservative downside estimate
2. **Realistic Scenario**: Most likely outcome based on current trends
3. **Optimistic Scenario**: Upside potential with favorable conditions

For EACH scenario, provide:
- Target price at end of Q1 and Q2
- Confidence percentage (0-100%)
- Key assumptions driving the scenario
- Main risk factors

Format response as JSON:
{
  "q1_forecast": {
    "pessimistic": {"price": X, "confidence": Y, "assumptions": "...", "risks": "..."},
    "realistic": {"price": X, "confidence": Y, "assumptions": "...", "risks": "..."},
    "optimistic": {"price": X, "confidence": Y, "assumptions": "...", "risks": "..."}
  },
  "q2_forecast": { ... same structure ... },
  "overall_outlook": "Brief 2-3 sentence summary"
}""",
        "template_variables": {
            "symbol": "string",
            "name": "string",
            "current_price": "decimal",
            "week_52_low": "decimal",
            "week_52_high": "decimal",
            "performance_30d": "decimal",
            "performance_90d": "decimal",
            "sector": "string",
            "asset_type": "string",
            "market_context": "string"
        }
    }
]
```

**Definition of Done**:
- [x] Database migration creates prompts and prompt_versions tables
- [x] Database migration creates analysis_results table
- [x] Default prompts seeded on first run
- [x] Template variable validation implemented
- [x] Alembic migration script created
- [x] Unit tests for schema (100% coverage)
- [x] Seed data loads successfully in dev environment

**Story Points**: 5
**Priority**: Must Have
**Dependencies**: F5.2-001 (Database Schema)
**Risk Level**: Low
**Assigned To**: Unassigned

---

### Story F8.1-002: Prompt CRUD API
**Status**: 🔴 Not Started
**User Story**: As FX, I want to create, read, update, and delete prompts so that I can customize my analysis over time

**Acceptance Criteria**:
- **Given** I want to manage prompts
- **When** I use the prompt API endpoints
- **Then** I can list all prompts with pagination
- **And** I can view a specific prompt by ID or name
- **And** I can create a new custom prompt
- **And** I can update an existing prompt (creates new version)
- **And** I can deactivate a prompt (soft delete)
- **And** I can view version history for any prompt
- **And** I can restore a previous version
- **And** template variables are validated on save

**API Endpoints**:
```python
# GET /api/prompts - List all active prompts
# GET /api/prompts/{id} - Get specific prompt
# GET /api/prompts/name/{name} - Get prompt by name
# POST /api/prompts - Create new prompt
# PUT /api/prompts/{id} - Update prompt (versions it)
# DELETE /api/prompts/{id} - Soft delete (is_active=false)
# GET /api/prompts/{id}/versions - Get version history
# POST /api/prompts/{id}/restore/{version} - Restore old version
```

**Request/Response Schema**:
```python
class PromptBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: Literal['global', 'position', 'forecast']
    prompt_text: str = Field(..., min_length=10)
    template_variables: Dict[str, str]  # {var_name: type}

class PromptCreate(PromptBase):
    pass

class PromptUpdate(PromptBase):
    change_reason: Optional[str] = None

class PromptResponse(PromptBase):
    id: int
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

class PromptVersionResponse(BaseModel):
    id: int
    prompt_id: int
    version: int
    prompt_text: str
    changed_by: Optional[str]
    changed_at: datetime
    change_reason: Optional[str]
```

**Service Layer**:
```python
class PromptService:
    def __init__(self, db: Session):
        self.db = db

    async def list_prompts(
        self,
        category: Optional[str] = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[Prompt]:
        # Query with filters

    async def get_prompt(self, prompt_id: int) -> Optional[Prompt]:
        # Get by ID

    async def get_prompt_by_name(self, name: str) -> Optional[Prompt]:
        # Get by unique name

    async def create_prompt(self, prompt_data: PromptCreate) -> Prompt:
        # Validate template variables
        # Create prompt
        # Create initial version record

    async def update_prompt(
        self,
        prompt_id: int,
        prompt_data: PromptUpdate,
        changed_by: str = "system"
    ) -> Prompt:
        # Increment version
        # Save old version to prompt_versions
        # Update prompt

    async def deactivate_prompt(self, prompt_id: int) -> bool:
        # Soft delete

    async def get_version_history(self, prompt_id: int) -> List[PromptVersion]:
        # Return all versions ordered by version DESC

    async def restore_version(self, prompt_id: int, version: int) -> Prompt:
        # Get old version from prompt_versions
        # Update prompt with old text
        # Increment version number
```

**Template Variable Validation**:
```python
VALID_TYPES = ['string', 'integer', 'decimal', 'boolean', 'array', 'object']

def validate_template_variables(template_vars: Dict[str, str]) -> bool:
    for var_name, var_type in template_vars.items():
        if not var_name.isidentifier():
            raise ValueError(f"Invalid variable name: {var_name}")
        if var_type not in VALID_TYPES:
            raise ValueError(f"Invalid type for {var_name}: {var_type}")
    return True

def validate_prompt_template(prompt_text: str, template_vars: Dict[str, str]):
    # Extract {variable} placeholders from prompt_text
    # Ensure all placeholders have corresponding template_vars
    # Warn about unused template_vars
```

**Definition of Done**:
- [x] All CRUD endpoints implemented
- [x] Service layer with business logic
- [x] Template variable validation
- [x] Version history tracking
- [x] Soft delete (deactivate) functionality
- [x] Version restoration
- [x] Input validation and error handling
- [x] Unit tests (≥85% coverage)
- [x] Integration tests for all endpoints
- [x] API documentation in OpenAPI

**Story Points**: 5
**Priority**: Must Have
**Dependencies**: F8.1-001 (Database Schema)
**Risk Level**: Low
**Assigned To**: Unassigned

---

### Story F8.1-003: Prompt Template Engine
**Status**: 🔴 Not Started
**User Story**: As the system, I want to render prompt templates with portfolio data so that prompts are contextually relevant

**Acceptance Criteria**:
- **Given** a prompt template with variables
- **When** rendering with portfolio data
- **Then** all template variables are replaced with actual values
- **And** missing variables raise clear errors
- **And** data types are validated (string, number, array, object)
- **And** arrays and objects are formatted readably
- **And** numbers are formatted with proper precision
- **And** rendering is safe from injection attacks

**Template Rendering Engine**:
```python
from string import Template
from typing import Any, Dict
from decimal import Decimal

class PromptRenderer:
    def __init__(self):
        self.formatters = {
            'decimal': self._format_decimal,
            'integer': self._format_integer,
            'array': self._format_array,
            'object': self._format_object,
            'string': str,
            'boolean': str
        }

    def render(
        self,
        prompt_text: str,
        template_vars: Dict[str, str],  # {var: type}
        data: Dict[str, Any]  # {var: value}
    ) -> str:
        # Validate all required variables present
        missing = set(template_vars.keys()) - set(data.keys())
        if missing:
            raise ValueError(f"Missing template variables: {missing}")

        # Format each value according to its type
        formatted_data = {}
        for var_name, var_type in template_vars.items():
            formatter = self.formatters.get(var_type)
            if not formatter:
                raise ValueError(f"Unknown type: {var_type}")
            formatted_data[var_name] = formatter(data[var_name])

        # Safe template substitution
        template = Template(prompt_text)
        return template.safe_substitute(formatted_data)

    def _format_decimal(self, value: Any) -> str:
        if isinstance(value, (int, float, Decimal)):
            return f"{Decimal(str(value)):.2f}"
        raise TypeError(f"Cannot format {value} as decimal")

    def _format_integer(self, value: Any) -> str:
        return str(int(value))

    def _format_array(self, value: list) -> str:
        # Format list as readable bullet points or comma-separated
        if not value:
            return "None"
        if len(value) <= 5:
            return ", ".join(str(v) for v in value)
        return f"{', '.join(str(v) for v in value[:5])} (and {len(value)-5} more)"

    def _format_object(self, value: dict) -> str:
        # Format dict as key: value pairs
        lines = [f"{k}: {v}" for k, v in value.items()]
        return "\n".join(lines)
```

**Example Usage**:
```python
renderer = PromptRenderer()

prompt_text = """
Portfolio Value: ${portfolio_value}
Positions: {position_count}
Top Holdings: {top_holdings}
"""

template_vars = {
    "portfolio_value": "decimal",
    "position_count": "integer",
    "top_holdings": "array"
}

data = {
    "portfolio_value": Decimal("50000.50"),
    "position_count": 15,
    "top_holdings": ["AAPL", "TSLA", "BTC", "ETH"]
}

rendered = renderer.render(prompt_text, template_vars, data)
# Output:
# Portfolio Value: $50000.50
# Positions: 15
# Top Holdings: AAPL, TSLA, BTC, ETH
```

**Data Collection Service**:
```python
class PromptDataCollector:
    """Collect portfolio data for template rendering"""

    def __init__(self, db: Session, portfolio_service: PortfolioService):
        self.db = db
        self.portfolio_service = portfolio_service

    async def collect_global_data(self) -> Dict[str, Any]:
        """Collect data for global market analysis prompt"""
        summary = await self.portfolio_service.get_open_positions_summary()
        positions = await self.portfolio_service.get_all_positions()

        return {
            "portfolio_value": summary.total_value,
            "asset_allocation": {
                "stocks": summary.stocks_value,
                "crypto": summary.crypto_value,
                "metals": summary.metals_value
            },
            "position_count": len(positions),
            "top_holdings": [
                f"{p.symbol} ({p.current_value:.2f})"
                for p in sorted(positions, key=lambda x: x.current_value, reverse=True)[:5]
            ]
        }

    async def collect_position_data(self, symbol: str) -> Dict[str, Any]:
        """Collect data for position-specific analysis"""
        position = await self.portfolio_service.get_position(symbol)
        price_data = await self.yahoo_service.get_price(symbol)

        return {
            "symbol": position.symbol,
            "name": position.name or position.symbol,
            "quantity": position.quantity,
            "current_price": position.current_price,
            "cost_basis": position.total_cost_basis,
            "unrealized_pnl": position.unrealized_pnl,
            "pnl_percentage": position.unrealized_pnl_percentage,
            "position_percentage": position.portfolio_percentage,
            "day_change": price_data.day_change_percent,
            "sector": price_data.sector or "N/A",
            "asset_type": position.asset_type
        }
```

**Definition of Done**:
- [x] Template rendering engine implemented
- [x] Type-specific formatters for all supported types
- [x] Input validation and error handling
- [x] Data collection service for global/position data
- [x] Safe template substitution (no injection)
- [x] Unit tests (≥85% coverage)
- [x] Integration tests with real prompts
- [x] Performance: Render in <50ms

**Story Points**: 3
**Priority**: Must Have
**Dependencies**: F8.1-002 (Prompt CRUD)
**Risk Level**: Low
**Assigned To**: Unassigned

---

## Feature 8.2: Anthropic Claude Integration
**Feature Description**: Core integration with Anthropic Claude API for generating market analysis
**User Value**: Access to state-of-the-art AI analysis of market conditions and portfolio
**Priority**: High (Enables all analysis features)
**Complexity**: 13 story points

### Story F8.2-001: Claude API Client
**Status**: 🔴 Not Started
**User Story**: As the system, I want to communicate with Claude API so that I can generate market analysis

**Acceptance Criteria**:
- **Given** the Anthropic Claude API
- **When** sending analysis requests
- **Then** responses are received successfully
- **And** API key is securely managed via environment variables
- **And** rate limiting is respected (50 requests/minute for tier 1)
- **And** token usage is tracked and logged
- **And** errors are handled gracefully with retries
- **And** streaming responses are supported for long analyses
- **And** timeout configuration is set to 30 seconds

**Dependencies**:
```toml
# pyproject.toml
[project]
dependencies = [
    "anthropic>=0.18.0",
    "httpx>=0.25.0",  # For async HTTP
]
```

**Configuration**:
```python
# backend/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Existing settings...

    # Anthropic Claude Configuration
    ANTHROPIC_API_KEY: str
    ANTHROPIC_MODEL: str = "claude-sonnet-4-5-20250929"  # Latest Sonnet
    ANTHROPIC_MAX_TOKENS: int = 4096
    ANTHROPIC_TEMPERATURE: float = 0.3  # Lower for more factual analysis
    ANTHROPIC_TIMEOUT: int = 30  # seconds
    ANTHROPIC_MAX_RETRIES: int = 3
    ANTHROPIC_RATE_LIMIT: int = 50  # requests per minute

    class Config:
        env_file = ".env"
```

**Claude Service Implementation**:
```python
from anthropic import Anthropic, AsyncAnthropic
from typing import Optional, Dict, Any
import asyncio
import time
from collections import deque

class ClaudeService:
    def __init__(self, config: Settings):
        self.client = AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
        self.model = config.ANTHROPIC_MODEL
        self.max_tokens = config.ANTHROPIC_MAX_TOKENS
        self.temperature = config.ANTHROPIC_TEMPERATURE
        self.timeout = config.ANTHROPIC_TIMEOUT
        self.max_retries = config.ANTHROPIC_MAX_RETRIES

        # Rate limiting
        self.rate_limit = config.ANTHROPIC_RATE_LIMIT
        self.request_times = deque(maxlen=self.rate_limit)

    async def generate_analysis(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate analysis using Claude API

        Returns:
            {
                'content': str,  # Analysis text
                'tokens_used': int,  # Total tokens
                'model': str,  # Model used
                'generation_time_ms': int  # Time taken
            }
        """
        await self._check_rate_limit()

        start_time = time.time()

        # Build message
        messages = [{"role": "user", "content": prompt}]

        # Retry logic with exponential backoff
        for attempt in range(self.max_retries):
            try:
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens or self.max_tokens,
                    temperature=temperature or self.temperature,
                    system=system_prompt or self._default_system_prompt(),
                    messages=messages,
                    timeout=self.timeout
                )

                end_time = time.time()

                return {
                    'content': response.content[0].text,
                    'tokens_used': response.usage.input_tokens + response.usage.output_tokens,
                    'model': response.model,
                    'generation_time_ms': int((end_time - start_time) * 1000),
                    'stop_reason': response.stop_reason
                }

            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise

                # Exponential backoff: 1s, 2s, 4s
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)

        raise Exception("Max retries exceeded")

    async def _check_rate_limit(self):
        """Ensure we don't exceed rate limits"""
        now = time.time()

        # Remove requests older than 1 minute
        while self.request_times and now - self.request_times[0] > 60:
            self.request_times.popleft()

        # If at limit, wait
        if len(self.request_times) >= self.rate_limit:
            sleep_time = 60 - (now - self.request_times[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

        self.request_times.append(now)

    def _default_system_prompt(self) -> str:
        return """You are a professional financial analyst providing market insights for a portfolio management application.

Your analysis should be:
- Data-driven and factual
- Concise and actionable
- Focused on the specific portfolio context provided
- Free from disclaimers (user understands this is AI analysis)
- Formatted in clear, readable markdown

Avoid generic advice. Focus on specific insights relevant to the user's holdings."""

```

**Error Handling**:
```python
class ClaudeAPIError(Exception):
    """Base exception for Claude API errors"""
    pass

class RateLimitError(ClaudeAPIError):
    """Rate limit exceeded"""
    pass

class InvalidResponseError(ClaudeAPIError):
    """Response format invalid"""
    pass

# Usage in service
try:
    result = await claude_service.generate_analysis(prompt)
except anthropic.RateLimitError as e:
    raise RateLimitError("Rate limit exceeded, try again later")
except anthropic.APITimeoutError as e:
    raise ClaudeAPIError(f"Request timeout: {e}")
except Exception as e:
    logger.error(f"Claude API error: {e}")
    raise ClaudeAPIError(f"Analysis generation failed: {e}")
```

**Definition of Done**:
- [x] Anthropic SDK installed and configured
- [x] ClaudeService class with async support
- [x] Rate limiting implementation
- [x] Retry logic with exponential backoff
- [x] Token usage tracking
- [x] Error handling for all API errors
- [x] Environment variable configuration
- [x] Unit tests with mocked API (≥85% coverage)
- [x] Integration test with real API (manual)
- [x] Logging for debugging and monitoring

**Story Points**: 8
**Priority**: Must Have
**Dependencies**: None (foundation)
**Risk Level**: Medium (external API dependency)
**Assigned To**: Unassigned

---

### Story F8.2-002: Analysis Service Layer
**Status**: 🔴 Not Started
**User Story**: As the system, I want a service layer that orchestrates prompt rendering and Claude API calls for analysis generation

**Acceptance Criteria**:
- **Given** a request for analysis
- **When** generating analysis
- **Then** the correct prompt is fetched from database
- **And** portfolio data is collected and rendered into prompt
- **And** Claude API is called with rendered prompt
- **And** response is parsed and validated
- **And** analysis is stored in database with metadata
- **And** cached analyses are returned if recent (< 1 hour)
- **And** all operations are logged for debugging

**Analysis Service**:
```python
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import json

class AnalysisService:
    def __init__(
        self,
        db: Session,
        claude_service: ClaudeService,
        prompt_service: PromptService,
        data_collector: PromptDataCollector,
        cache_service: CacheService
    ):
        self.db = db
        self.claude = claude_service
        self.prompts = prompt_service
        self.data = data_collector
        self.cache = cache_service

    async def generate_global_analysis(
        self,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Generate global market analysis for entire portfolio

        Returns:
            {
                'analysis': str,  # Markdown analysis text
                'generated_at': datetime,
                'tokens_used': int,
                'cached': bool
            }
        """
        cache_key = "analysis:global"

        # Check cache first
        if not force_refresh:
            cached = await self._get_cached_analysis(cache_key)
            if cached:
                return {**cached, 'cached': True}

        # Fetch prompt
        prompt_template = await self.prompts.get_prompt_by_name("global_market_analysis")
        if not prompt_template:
            raise ValueError("Global analysis prompt not found")

        # Collect data
        data = await self.data.collect_global_data()

        # Render prompt
        renderer = PromptRenderer()
        rendered_prompt = renderer.render(
            prompt_template.prompt_text,
            prompt_template.template_variables,
            data
        )

        # Generate analysis
        result = await self.claude.generate_analysis(rendered_prompt)

        # Store in database
        analysis_record = AnalysisResult(
            analysis_type='global',
            symbol=None,
            prompt_id=prompt_template.id,
            prompt_version=prompt_template.version,
            raw_response=result['content'],
            parsed_data=None,  # No structured data for global
            tokens_used=result['tokens_used'],
            generation_time_ms=result['generation_time_ms'],
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        self.db.add(analysis_record)
        self.db.commit()

        # Cache for 1 hour
        analysis_data = {
            'analysis': result['content'],
            'generated_at': datetime.utcnow(),
            'tokens_used': result['tokens_used']
        }
        await self.cache.set(cache_key, analysis_data, ttl=3600)

        return {**analysis_data, 'cached': False}

    async def generate_position_analysis(
        self,
        symbol: str,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Generate analysis for specific position

        Returns same structure as global analysis
        """
        cache_key = f"analysis:position:{symbol}"

        if not force_refresh:
            cached = await self._get_cached_analysis(cache_key)
            if cached:
                return {**cached, 'cached': True}

        # Fetch prompt
        prompt_template = await self.prompts.get_prompt_by_name("position_analysis")

        # Collect position data
        data = await self.data.collect_position_data(symbol)

        # Render and generate
        renderer = PromptRenderer()
        rendered_prompt = renderer.render(
            prompt_template.prompt_text,
            prompt_template.template_variables,
            data
        )

        result = await self.claude.generate_analysis(rendered_prompt)

        # Parse recommendation if present
        parsed_data = self._extract_recommendation(result['content'])

        # Store in database
        analysis_record = AnalysisResult(
            analysis_type='position',
            symbol=symbol,
            prompt_id=prompt_template.id,
            prompt_version=prompt_template.version,
            raw_response=result['content'],
            parsed_data=parsed_data,
            tokens_used=result['tokens_used'],
            generation_time_ms=result['generation_time_ms'],
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        self.db.add(analysis_record)
        self.db.commit()

        analysis_data = {
            'analysis': result['content'],
            'recommendation': parsed_data.get('recommendation'),
            'generated_at': datetime.utcnow(),
            'tokens_used': result['tokens_used']
        }
        await self.cache.set(cache_key, analysis_data, ttl=3600)

        return {**analysis_data, 'cached': False}

    async def generate_forecast(
        self,
        symbol: str,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Generate two-quarter forecast with scenarios

        Returns:
            {
                'q1_forecast': {...},
                'q2_forecast': {...},
                'overall_outlook': str,
                'generated_at': datetime,
                'tokens_used': int,
                'cached': bool
            }
        """
        cache_key = f"analysis:forecast:{symbol}"

        if not force_refresh:
            cached = await self._get_cached_analysis(cache_key)
            if cached:
                return {**cached, 'cached': True}

        # Fetch prompt
        prompt_template = await self.prompts.get_prompt_by_name("forecast_two_quarters")

        # Collect forecast data (position + market context)
        data = await self.data.collect_forecast_data(symbol)

        # Render and generate
        renderer = PromptRenderer()
        rendered_prompt = renderer.render(
            prompt_template.prompt_text,
            prompt_template.template_variables,
            data
        )

        # Request JSON response
        result = await self.claude.generate_analysis(
            rendered_prompt,
            temperature=0.1  # Lower for more consistent JSON
        )

        # Parse JSON forecast
        try:
            forecast_data = json.loads(result['content'])
        except json.JSONDecodeError:
            # Fallback: extract JSON from markdown code block
            forecast_data = self._extract_json_from_response(result['content'])

        # Validate forecast structure
        self._validate_forecast(forecast_data)

        # Store in database
        analysis_record = AnalysisResult(
            analysis_type='forecast',
            symbol=symbol,
            prompt_id=prompt_template.id,
            prompt_version=prompt_template.version,
            raw_response=result['content'],
            parsed_data=forecast_data,
            tokens_used=result['tokens_used'],
            generation_time_ms=result['generation_time_ms'],
            expires_at=datetime.utcnow() + timedelta(hours=24)  # Longer TTL for forecasts
        )
        self.db.add(analysis_record)
        self.db.commit()

        response = {
            **forecast_data,
            'generated_at': datetime.utcnow(),
            'tokens_used': result['tokens_used'],
            'cached': False
        }

        await self.cache.set(cache_key, response, ttl=86400)  # 24 hours

        return response

    async def _get_cached_analysis(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Check Redis cache for recent analysis"""
        cached = await self.cache.get(cache_key)
        if cached:
            # Check if still valid (< 1 hour old for analysis, < 24h for forecast)
            age = datetime.utcnow() - cached['generated_at']
            max_age = timedelta(hours=24) if 'forecast' in cache_key else timedelta(hours=1)
            if age < max_age:
                return cached
        return None

    def _extract_recommendation(self, analysis_text: str) -> Dict[str, Any]:
        """Extract HOLD/BUY/SELL recommendation from analysis"""
        recommendations = ['HOLD', 'BUY_MORE', 'REDUCE', 'SELL']
        for rec in recommendations:
            if rec in analysis_text.upper():
                return {'recommendation': rec}
        return {}

    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from markdown code block"""
        import re
        json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        raise ValueError("No JSON found in response")

    def _validate_forecast(self, forecast: Dict[str, Any]):
        """Validate forecast structure"""
        required_keys = ['q1_forecast', 'q2_forecast', 'overall_outlook']
        if not all(k in forecast for k in required_keys):
            raise ValueError(f"Forecast missing required keys: {required_keys}")

        for quarter in ['q1_forecast', 'q2_forecast']:
            scenarios = forecast[quarter]
            for scenario in ['pessimistic', 'realistic', 'optimistic']:
                if scenario not in scenarios:
                    raise ValueError(f"{quarter} missing {scenario} scenario")

                scenario_data = scenarios[scenario]
                if 'price' not in scenario_data or 'confidence' not in scenario_data:
                    raise ValueError(f"{quarter}.{scenario} missing price or confidence")
```

**Definition of Done**:
- [x] AnalysisService class implemented
- [x] Global analysis generation
- [x] Position analysis generation
- [x] Forecast generation with JSON parsing
- [x] Cache integration (Redis)
- [x] Database storage of results
- [x] Error handling and validation
- [x] Unit tests (≥85% coverage)
- [x] Integration tests
- [x] Performance: <10s for global, <5s for position

**Story Points**: 5
**Priority**: Must Have
**Dependencies**: F8.1-003 (Template Engine), F8.2-001 (Claude Client)
**Risk Level**: Medium
**Assigned To**: Unassigned

---

## Feature 8.3: Global Market Analysis
**Feature Description**: Portfolio-wide market analysis providing overall market sentiment and macro insights
**User Value**: Understand broader market conditions affecting entire portfolio
**Priority**: High
**Complexity**: 8 story points

### Story F8.3-001: Global Analysis API
**Status**: 🔴 Not Started
**User Story**: As FX, I want to request a global market analysis so that I understand overall market conditions

**Acceptance Criteria**:
- **Given** I have an active portfolio
- **When** I request global analysis
- **Then** I receive comprehensive market analysis in <10 seconds
- **And** analysis covers current market sentiment
- **And** analysis includes macro-economic factors
- **And** analysis provides sector insights relevant to my holdings
- **And** analysis identifies key risks to monitor
- **And** cached analysis is returned if recent (< 1 hour)
- **And** I can force refresh to get new analysis

**API Endpoint**:
```python
@router.get("/api/analysis/global", response_model=GlobalAnalysisResponse)
async def get_global_analysis(
    force_refresh: bool = Query(False, description="Force new analysis generation"),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Get global market analysis for entire portfolio

    Returns cached analysis if available and recent (< 1 hour),
    otherwise generates new analysis.
    """
    result = await analysis_service.generate_global_analysis(force_refresh)
    return GlobalAnalysisResponse(**result)
```

**Response Model**:
```python
class GlobalAnalysisResponse(BaseModel):
    analysis: str = Field(..., description="Markdown-formatted analysis")
    generated_at: datetime
    tokens_used: int
    cached: bool = Field(..., description="Whether this was served from cache")

    class Config:
        json_schema_extra = {
            "example": {
                "analysis": "## Market Sentiment\n\nCurrent markets showing...",
                "generated_at": "2025-01-15T10:30:00Z",
                "tokens_used": 1523,
                "cached": False
            }
        }
```

**Definition of Done**:
- [x] API endpoint implemented
- [x] Response model with proper typing
- [x] Cache integration (1-hour TTL)
- [x] Force refresh parameter
- [x] Error handling with proper status codes
- [x] Unit tests (≥85% coverage)
- [x] Integration tests with mock service
- [x] API documentation in OpenAPI
- [x] Performance: <10s for fresh, <100ms for cached

**Story Points**: 3
**Priority**: Must Have
**Dependencies**: F8.2-002 (Analysis Service)
**Risk Level**: Low
**Assigned To**: Unassigned

---

### Story F8.3-002: Market Context Data Collection
**Status**: 🔴 Not Started
**User Story**: As the system, I want to collect comprehensive market context so that global analysis is well-informed

**Acceptance Criteria**:
- **Given** the need for global analysis
- **When** collecting market context
- **Then** current portfolio composition is included
- **And** top holdings by value are identified
- **And** sector allocation percentages are calculated
- **And** recent P&L trends are summarized
- **And** market indices (S&P 500, BTC, Gold) are referenced
- **And** data collection completes in <2 seconds

**Data Collection Enhancement**:
```python
# Extend PromptDataCollector from F8.1-003

class PromptDataCollector:
    # ... existing methods ...

    async def collect_global_data(self) -> Dict[str, Any]:
        """Enhanced global data collection with market context"""
        summary = await self.portfolio_service.get_open_positions_summary()
        positions = await self.portfolio_service.get_all_positions()

        # Sector allocation
        sector_allocation = self._calculate_sector_allocation(positions)

        # Recent performance (last 24h, 7d, 30d)
        performance = await self._get_portfolio_performance()

        # Market indices for context
        indices = await self._get_market_indices()

        # Top holdings
        sorted_positions = sorted(positions, key=lambda x: x.current_value, reverse=True)
        top_holdings = [
            {
                'symbol': p.symbol,
                'value': float(p.current_value),
                'allocation': float(p.portfolio_percentage),
                'pnl': float(p.unrealized_pnl_percentage)
            }
            for p in sorted_positions[:10]
        ]

        return {
            "portfolio_value": float(summary.total_value),
            "asset_allocation": {
                "stocks": float(summary.stocks_value),
                "stocks_pct": float(summary.stocks_percentage),
                "crypto": float(summary.crypto_value),
                "crypto_pct": float(summary.crypto_percentage),
                "metals": float(summary.metals_value),
                "metals_pct": float(summary.metals_percentage)
            },
            "sector_allocation": sector_allocation,
            "position_count": len(positions),
            "top_holdings": self._format_holdings_list(top_holdings),
            "performance": performance,
            "market_indices": indices,
            "total_unrealized_pnl": float(summary.total_unrealized_pnl),
            "total_unrealized_pnl_pct": float(summary.total_unrealized_pnl_percentage)
        }

    def _calculate_sector_allocation(self, positions: List[Position]) -> Dict[str, float]:
        """Calculate portfolio allocation by sector"""
        # Group by sector (would need sector data from Yahoo Finance)
        # For now, group by asset type as proxy
        total_value = sum(p.current_value for p in positions)
        sectors = {}

        for p in positions:
            sector = p.sector or p.asset_type  # Fallback to asset_type
            if sector not in sectors:
                sectors[sector] = 0
            sectors[sector] += float(p.current_value)

        # Convert to percentages
        return {
            sector: round(value / float(total_value) * 100, 2)
            for sector, value in sectors.items()
        }

    async def _get_portfolio_performance(self) -> Dict[str, Any]:
        """Get portfolio performance over different time periods"""
        # This would require historical price_history data
        # For MVP, return current P&L
        summary = await self.portfolio_service.get_open_positions_summary()

        return {
            "current_pnl": float(summary.total_unrealized_pnl),
            "current_pnl_pct": float(summary.total_unrealized_pnl_percentage),
            # Future: 24h, 7d, 30d historical changes
        }

    async def _get_market_indices(self) -> Dict[str, Any]:
        """Fetch major market indices for context"""
        indices_symbols = ['^GSPC', '^DJI', 'BTC-USD', 'GC=F']  # S&P, Dow, Bitcoin, Gold
        indices_data = {}

        for symbol in indices_symbols:
            try:
                price_data = await self.yahoo_service.get_price(symbol)
                indices_data[symbol] = {
                    'price': float(price_data.current_price),
                    'change': float(price_data.day_change_percent)
                }
            except:
                pass  # Skip if unavailable

        return indices_data

    def _format_holdings_list(self, holdings: List[Dict]) -> str:
        """Format top holdings as readable string"""
        lines = []
        for h in holdings:
            lines.append(
                f"{h['symbol']}: €{h['value']:.2f} ({h['allocation']:.1f}% of portfolio, "
                f"{h['pnl']:+.2f}% P&L)"
            )
        return "\n".join(lines)
```

**Definition of Done**:
- [x] Enhanced data collection with market context
- [x] Sector allocation calculation
- [x] Market indices fetching
- [x] Performance metrics aggregation
- [x] Top holdings formatting
- [x] Unit tests (≥85% coverage)
- [x] Performance: <2s data collection
- [x] Graceful handling of missing data

**Story Points**: 5
**Priority**: Must Have
**Dependencies**: F2.2-001 (Portfolio Service), F3.1-001 (Yahoo Finance)
**Risk Level**: Low
**Assigned To**: Unassigned

---

## Feature 8.4: Position-Level Analysis
**Feature Description**: AI analysis for individual positions with specific recommendations
**User Value**: Get actionable insights on each investment holding
**Priority**: High
**Complexity**: 10 story points

### Story F8.4-001: Position Analysis API
**Status**: 🔴 Not Started
**User Story**: As FX, I want analysis for individual positions so that I can make informed decisions about each holding

**Acceptance Criteria**:
- **Given** I have a specific position
- **When** I request analysis for that position
- **Then** I receive detailed analysis in <5 seconds
- **And** analysis includes current performance assessment
- **And** analysis identifies key factors affecting the asset
- **And** analysis provides risk assessment
- **And** analysis includes a recommendation: HOLD, BUY_MORE, REDUCE, or SELL
- **And** cached analysis is returned if recent (< 1 hour)

**API Endpoint**:
```python
@router.get("/api/analysis/position/{symbol}", response_model=PositionAnalysisResponse)
async def get_position_analysis(
    symbol: str = Path(..., description="Asset symbol"),
    force_refresh: bool = Query(False),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Get AI analysis for specific position

    Includes market assessment, risk evaluation, and recommendation.
    """
    result = await analysis_service.generate_position_analysis(symbol, force_refresh)
    return PositionAnalysisResponse(**result)
```

**Response Model**:
```python
from enum import Enum

class Recommendation(str, Enum):
    HOLD = "HOLD"
    BUY_MORE = "BUY_MORE"
    REDUCE = "REDUCE"
    SELL = "SELL"

class PositionAnalysisResponse(BaseModel):
    analysis: str = Field(..., description="Markdown-formatted analysis")
    recommendation: Optional[Recommendation] = Field(
        None,
        description="Extracted recommendation"
    )
    generated_at: datetime
    tokens_used: int
    cached: bool

    class Config:
        json_schema_extra = {
            "example": {
                "analysis": "## Current Position\n\nBTC is currently...",
                "recommendation": "HOLD",
                "generated_at": "2025-01-15T10:35:00Z",
                "tokens_used": 856,
                "cached": False
            }
        }
```

**Bulk Analysis Endpoint**:
```python
@router.post("/api/analysis/positions/bulk", response_model=BulkAnalysisResponse)
async def get_bulk_position_analysis(
    symbols: List[str] = Body(..., max_items=10),
    force_refresh: bool = Query(False),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Get analysis for multiple positions (max 10)

    Useful for analyzing entire portfolio in one request.
    """
    results = await asyncio.gather(*[
        analysis_service.generate_position_analysis(symbol, force_refresh)
        for symbol in symbols
    ])

    return BulkAnalysisResponse(
        analyses={
            symbol: PositionAnalysisResponse(**result)
            for symbol, result in zip(symbols, results)
        },
        total_tokens_used=sum(r['tokens_used'] for r in results)
    )

class BulkAnalysisResponse(BaseModel):
    analyses: Dict[str, PositionAnalysisResponse]
    total_tokens_used: int
```

**Definition of Done**:
- [x] Single position analysis endpoint
- [x] Bulk analysis endpoint (max 10)
- [x] Recommendation extraction
- [x] Response models with typing
- [x] Cache integration
- [x] Error handling (position not found)
- [x] Unit tests (≥85% coverage)
- [x] Integration tests
- [x] API documentation
- [x] Performance: <5s per position

**Story Points**: 5
**Priority**: Must Have
**Dependencies**: F8.2-002 (Analysis Service)
**Risk Level**: Low
**Assigned To**: Unassigned

---

### Story F8.4-002: Position Context Enhancement
**Status**: 🔴 Not Started
**User Story**: As the system, I want rich position context so that Claude can provide insightful analysis

**Acceptance Criteria**:
- **Given** a position analysis request
- **When** collecting data for the prompt
- **Then** current position details are included
- **And** cost basis and P&L are provided
- **And** recent price performance is included (24h, 7d, 30d)
- **And** sector and industry info is fetched
- **And** 52-week high/low range is provided
- **And** volume and liquidity metrics are included
- **And** data collection completes in <2 seconds

**Enhanced Position Data Collection**:
```python
# Extend PromptDataCollector

async def collect_position_data(self, symbol: str) -> Dict[str, Any]:
    """Enhanced position data with rich market context"""
    # Get position from database
    position = await self.portfolio_service.get_position(symbol)
    if not position:
        raise ValueError(f"Position not found: {symbol}")

    # Get current price data
    price_data = await self.yahoo_service.get_price(symbol)

    # Get historical performance
    performance = await self._get_position_performance(symbol)

    # Get fundamental data (if stock)
    fundamentals = {}
    if position.asset_type == 'stocks':
        fundamentals = await self._get_stock_fundamentals(symbol)

    return {
        # Position basics
        "symbol": position.symbol,
        "name": fundamentals.get('name') or position.symbol,
        "quantity": float(position.quantity),
        "current_price": float(position.current_price),
        "cost_basis": float(position.total_cost_basis),
        "avg_cost_per_unit": float(position.average_cost_per_unit),

        # P&L
        "unrealized_pnl": float(position.unrealized_pnl),
        "pnl_percentage": float(position.unrealized_pnl_percentage),
        "position_percentage": float(position.portfolio_percentage),

        # Market data
        "day_change": float(price_data.day_change_percent),
        "previous_close": float(price_data.previous_close),

        # Performance metrics
        "performance_24h": performance.get('24h', 0),
        "performance_7d": performance.get('7d', 0),
        "performance_30d": performance.get('30d', 0),

        # Market context
        "week_52_low": float(fundamentals.get('fiftyTwoWeekLow', 0)),
        "week_52_high": float(fundamentals.get('fiftyTwoWeekHigh', 0)),
        "volume": fundamentals.get('volume', 0),
        "avg_volume": fundamentals.get('averageVolume', 0),

        # Classification
        "sector": fundamentals.get('sector', 'N/A'),
        "industry": fundamentals.get('industry', 'N/A'),
        "asset_type": position.asset_type,

        # Transaction context
        "transaction_count": await self._get_transaction_count(symbol),
        "first_purchase_date": await self._get_first_purchase_date(symbol),
        "holding_period_days": await self._get_holding_period(symbol)
    }

async def _get_stock_fundamentals(self, symbol: str) -> Dict[str, Any]:
    """Fetch fundamental data from Yahoo Finance"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        return {
            'name': info.get('longName', symbol),
            'sector': info.get('sector'),
            'industry': info.get('industry'),
            'fiftyTwoWeekLow': info.get('fiftyTwoWeekLow'),
            'fiftyTwoWeekHigh': info.get('fiftyTwoWeekHigh'),
            'volume': info.get('volume'),
            'averageVolume': info.get('averageVolume'),
            'marketCap': info.get('marketCap'),
            'peRatio': info.get('trailingPE')
        }
    except:
        return {}

async def _get_position_performance(self, symbol: str) -> Dict[str, float]:
    """Calculate position performance over different periods"""
    # Would use price_history table if available
    # For MVP, return placeholder
    return {
        '24h': 0.0,
        '7d': 0.0,
        '30d': 0.0
    }

async def _get_transaction_count(self, symbol: str) -> int:
    """Get number of transactions for this position"""
    result = self.db.execute(
        text("SELECT COUNT(*) FROM transactions WHERE symbol = :symbol"),
        {"symbol": symbol}
    )
    return result.scalar() or 0

async def _get_first_purchase_date(self, symbol: str) -> Optional[datetime]:
    """Get date of first purchase"""
    result = self.db.execute(
        text("""
            SELECT MIN(transaction_date)
            FROM transactions
            WHERE symbol = :symbol
            AND transaction_type IN ('BUY', 'DEPOSIT')
        """),
        {"symbol": symbol}
    )
    return result.scalar()

async def _get_holding_period(self, symbol: str) -> int:
    """Calculate days since first purchase"""
    first_date = await self._get_first_purchase_date(symbol)
    if first_date:
        return (datetime.utcnow() - first_date).days
    return 0
```

**Definition of Done**:
- [x] Enhanced position data collection
- [x] Yahoo Finance fundamentals integration
- [x] Performance metrics calculation
- [x] Transaction context (count, first purchase, holding period)
- [x] 52-week range and volume metrics
- [x] Sector/industry classification
- [x] Error handling for missing data
- [x] Unit tests (≥85% coverage)
- [x] Performance: <2s data collection

**Story Points**: 5
**Priority**: Must Have
**Dependencies**: F3.1-001 (Yahoo Finance), F2.2-001 (Portfolio Service)
**Risk Level**: Low
**Assigned To**: Unassigned

---

## Feature 8.5: Forecasting Engine with Scenarios
**Feature Description**: Generate two-quarter forecasts with pessimistic, realistic, and optimistic scenarios
**User Value**: Make informed decisions based on data-driven predictions
**Priority**: High (Core differentiator)
**Complexity**: 15 story points

### Story F8.5-001: Forecast API
**Status**: 🔴 Not Started
**User Story**: As FX, I want two-quarter forecasts for my positions so that I can plan my investment strategy

**Acceptance Criteria**:
- **Given** I have a position
- **When** I request a forecast
- **Then** I receive Q1 and Q2 predictions
- **And** each quarter has pessimistic, realistic, and optimistic scenarios
- **And** each scenario includes target price and confidence %
- **And** each scenario includes key assumptions
- **And** each scenario includes risk factors
- **And** forecast is generated in <15 seconds
- **And** cached forecasts are returned if recent (< 24 hours)

**API Endpoint**:
```python
@router.get("/api/analysis/forecast/{symbol}", response_model=ForecastResponse)
async def get_forecast(
    symbol: str = Path(..., description="Asset symbol"),
    force_refresh: bool = Query(False),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Get two-quarter forecast with scenarios

    Returns pessimistic, realistic, and optimistic scenarios
    for Q1 and Q2 with confidence levels.
    """
    result = await analysis_service.generate_forecast(symbol, force_refresh)
    return ForecastResponse(**result)
```

**Response Models**:
```python
class ScenarioForecast(BaseModel):
    price: Decimal = Field(..., description="Target price for this scenario")
    confidence: int = Field(..., ge=0, le=100, description="Confidence percentage")
    assumptions: str = Field(..., description="Key assumptions driving this scenario")
    risks: str = Field(..., description="Main risk factors")

class QuarterForecast(BaseModel):
    pessimistic: ScenarioForecast
    realistic: ScenarioForecast
    optimistic: ScenarioForecast

class ForecastResponse(BaseModel):
    symbol: str
    current_price: Decimal
    q1_forecast: QuarterForecast
    q2_forecast: QuarterForecast
    overall_outlook: str = Field(..., description="2-3 sentence summary")
    generated_at: datetime
    tokens_used: int
    cached: bool

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTC-USD",
                "current_price": 45000.00,
                "q1_forecast": {
                    "pessimistic": {
                        "price": 38000.00,
                        "confidence": 70,
                        "assumptions": "Regulatory headwinds and risk-off sentiment",
                        "risks": "SEC enforcement actions, macro recession"
                    },
                    "realistic": {
                        "price": 52000.00,
                        "confidence": 65,
                        "assumptions": "Continued institutional adoption, ETF inflows",
                        "risks": "Market volatility, liquidity concerns"
                    },
                    "optimistic": {
                        "price": 68000.00,
                        "confidence": 45,
                        "assumptions": "Major institutional announcements, spot ETF approval",
                        "risks": "Overheating, regulatory surprise"
                    }
                },
                "q2_forecast": "{ ... similar structure ... }",
                "overall_outlook": "Bitcoin faces near-term volatility but strong fundamentals support medium-term upside. Institutional adoption remains key driver.",
                "generated_at": "2025-01-15T10:40:00Z",
                "tokens_used": 2156,
                "cached": False
            }
        }
```

**Bulk Forecast Endpoint**:
```python
@router.post("/api/analysis/forecasts/bulk", response_model=BulkForecastResponse)
async def get_bulk_forecasts(
    symbols: List[str] = Body(..., max_items=5),  # Limit to 5 for token management
    force_refresh: bool = Query(False),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Get forecasts for multiple positions (max 5)

    Use for portfolio-wide forecast generation.
    """
    results = await asyncio.gather(*[
        analysis_service.generate_forecast(symbol, force_refresh)
        for symbol in symbols
    ])

    return BulkForecastResponse(
        forecasts={
            symbol: ForecastResponse(**result)
            for symbol, result in zip(symbols, results)
        },
        total_tokens_used=sum(r['tokens_used'] for r in results)
    )

class BulkForecastResponse(BaseModel):
    forecasts: Dict[str, ForecastResponse]
    total_tokens_used: int
```

**Definition of Done**:
- [x] Single forecast endpoint
- [x] Bulk forecast endpoint (max 5)
- [x] Response models with validation
- [x] JSON parsing from Claude response
- [x] Forecast structure validation
- [x] Cache integration (24-hour TTL)
- [x] Error handling
- [x] Unit tests (≥85% coverage)
- [x] Integration tests
- [x] API documentation
- [x] Performance: <15s per forecast

**Story Points**: 8
**Priority**: Must Have
**Dependencies**: F8.2-002 (Analysis Service)
**Risk Level**: Medium (JSON parsing complexity)
**Assigned To**: Unassigned

---

### Story F8.5-002: Forecast Data Collection
**Status**: 🔴 Not Started
**User Story**: As the system, I want comprehensive historical and market data so that forecasts are well-grounded

**Acceptance Criteria**:
- **Given** a forecast request
- **When** collecting data
- **Then** current price and position data are included
- **And** 52-week price range is provided
- **And** 30-day and 90-day performance is calculated
- **And** market context (sector performance, indices) is included
- **And** relevant news sentiment is considered (optional enhancement)
- **And** data collection completes in <3 seconds

**Forecast Data Collection**:
```python
# Extend PromptDataCollector

async def collect_forecast_data(self, symbol: str) -> Dict[str, Any]:
    """Collect comprehensive data for forecast generation"""
    # Get position data
    position_data = await self.collect_position_data(symbol)

    # Get historical prices
    historical = await self._get_historical_prices(symbol, days=365)

    # Calculate performance metrics
    performance = self._calculate_performance_metrics(historical)

    # Get market context
    market_context = await self._build_market_context(position_data['asset_type'])

    return {
        **position_data,
        "week_52_low": float(min(historical) if historical else 0),
        "week_52_high": float(max(historical) if historical else 0),
        "performance_30d": performance['30d'],
        "performance_90d": performance['90d'],
        "performance_180d": performance['180d'],
        "performance_365d": performance['365d'],
        "volatility_30d": performance['volatility'],
        "market_context": market_context
    }

async def _get_historical_prices(self, symbol: str, days: int) -> List[float]:
    """Fetch historical prices from Yahoo Finance"""
    try:
        ticker = yf.Ticker(symbol)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        hist = ticker.history(start=start_date, end=end_date)
        return hist['Close'].tolist()
    except:
        return []

def _calculate_performance_metrics(self, prices: List[float]) -> Dict[str, float]:
    """Calculate various performance metrics from price history"""
    if not prices or len(prices) < 30:
        return {
            '30d': 0.0, '90d': 0.0, '180d': 0.0, '365d': 0.0,
            'volatility': 0.0
        }

    current = prices[-1]

    # Performance calculations
    perf_30d = ((current - prices[-30]) / prices[-30] * 100) if len(prices) >= 30 else 0
    perf_90d = ((current - prices[-90]) / prices[-90] * 100) if len(prices) >= 90 else 0
    perf_180d = ((current - prices[-180]) / prices[-180] * 100) if len(prices) >= 180 else 0
    perf_365d = ((current - prices[0]) / prices[0] * 100) if len(prices) >= 365 else 0

    # Volatility (30-day standard deviation of returns)
    if len(prices) >= 30:
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(-30, 0)]
        volatility = (sum((r - sum(returns)/len(returns))**2 for r in returns) / len(returns)) ** 0.5 * 100
    else:
        volatility = 0.0

    return {
        '30d': round(perf_30d, 2),
        '90d': round(perf_90d, 2),
        '180d': round(perf_180d, 2),
        '365d': round(perf_365d, 2),
        'volatility': round(volatility, 2)
    }

async def _build_market_context(self, asset_type: str) -> str:
    """Build narrative market context based on asset type"""
    context_parts = []

    # Get relevant indices
    if asset_type == 'stocks':
        sp500 = await self.yahoo_service.get_price('^GSPC')
        context_parts.append(f"S&P 500: {sp500.day_change_percent:+.2f}% today")
    elif asset_type == 'crypto':
        btc = await self.yahoo_service.get_price('BTC-USD')
        context_parts.append(f"Bitcoin (market leader): {btc.day_change_percent:+.2f}% today")
    elif asset_type == 'metals':
        gold = await self.yahoo_service.get_price('GC=F')
        context_parts.append(f"Gold: {gold.day_change_percent:+.2f}% today")

    # Add macro context (could be enhanced with news API)
    context_parts.append("Current market sentiment: Mixed with volatility concerns")

    return ". ".join(context_parts)
```

**Definition of Done**:
- [x] Forecast data collection implemented
- [x] Historical price fetching (365 days)
- [x] Performance metrics calculation (30d, 90d, 180d, 365d)
- [x] Volatility calculation
- [x] Market context building
- [x] Error handling for missing data
- [x] Unit tests (≥85% coverage)
- [x] Performance: <3s data collection

**Story Points**: 5
**Priority**: Must Have
**Dependencies**: F3.1-001 (Yahoo Finance)
**Risk Level**: Low
**Assigned To**: Unassigned

---

### Story F8.5-003: Forecast Accuracy Tracking
**Status**: 🔴 Not Started
**User Story**: As FX, I want to track forecast accuracy over time so that I can trust the predictions

**Acceptance Criteria**:
- **Given** forecasts have been generated
- **When** actual prices are known (end of quarter)
- **Then** forecast accuracy is calculated
- **And** comparison shows which scenario was closest
- **And** accuracy percentage is stored for each forecast
- **And** I can view historical forecast performance
- **And** accuracy metrics are displayed per symbol
- **And** overall forecasting accuracy is tracked

**Forecast Tracking Schema**:
```sql
CREATE TABLE forecast_tracking (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    forecast_date DATE NOT NULL,
    quarter VARCHAR(10) NOT NULL,  -- 'Q1', 'Q2'

    -- Original forecast
    pessimistic_price DECIMAL(20, 8) NOT NULL,
    pessimistic_confidence INTEGER NOT NULL,
    realistic_price DECIMAL(20, 8) NOT NULL,
    realistic_confidence INTEGER NOT NULL,
    optimistic_price DECIMAL(20, 8) NOT NULL,
    optimistic_confidence INTEGER NOT NULL,

    -- Actual outcome
    actual_price DECIMAL(20, 8),
    actual_date DATE,

    -- Accuracy metrics
    closest_scenario VARCHAR(20),  -- 'pessimistic', 'realistic', 'optimistic'
    accuracy_percentage DECIMAL(5, 2),  -- How close was the best scenario
    realistic_error_percentage DECIMAL(6, 2),  -- Error of realistic scenario

    created_at TIMESTAMP DEFAULT NOW(),
    evaluated_at TIMESTAMP
);

CREATE INDEX idx_forecast_symbol ON forecast_tracking(symbol);
CREATE INDEX idx_forecast_date ON forecast_tracking(forecast_date);
```

**Tracking Service**:
```python
class ForecastTrackingService:
    def __init__(self, db: Session):
        self.db = db

    async def record_forecast(
        self,
        symbol: str,
        forecast_data: ForecastResponse
    ):
        """Store forecast for later accuracy evaluation"""
        # Calculate target dates (end of Q1/Q2)
        today = date.today()
        q1_end = self._get_quarter_end(today, 1)
        q2_end = self._get_quarter_end(today, 2)

        # Store Q1 forecast
        q1_tracking = ForecastTracking(
            symbol=symbol,
            forecast_date=today,
            quarter='Q1',
            pessimistic_price=forecast_data.q1_forecast.pessimistic.price,
            pessimistic_confidence=forecast_data.q1_forecast.pessimistic.confidence,
            realistic_price=forecast_data.q1_forecast.realistic.price,
            realistic_confidence=forecast_data.q1_forecast.realistic.confidence,
            optimistic_price=forecast_data.q1_forecast.optimistic.price,
            optimistic_confidence=forecast_data.q1_forecast.optimistic.confidence
        )
        self.db.add(q1_tracking)

        # Store Q2 forecast
        q2_tracking = ForecastTracking(
            symbol=symbol,
            forecast_date=today,
            quarter='Q2',
            pessimistic_price=forecast_data.q2_forecast.pessimistic.price,
            pessimistic_confidence=forecast_data.q2_forecast.pessimistic.confidence,
            realistic_price=forecast_data.q2_forecast.realistic.price,
            realistic_confidence=forecast_data.q2_forecast.realistic.confidence,
            optimistic_price=forecast_data.q2_forecast.optimistic.price,
            optimistic_confidence=forecast_data.q2_forecast.optimistic.confidence
        )
        self.db.add(q2_tracking)

        self.db.commit()

    async def evaluate_forecasts(self):
        """
        Evaluate accuracy of forecasts that have reached their target date

        Run this daily to check for forecasts ready to evaluate
        """
        today = date.today()

        # Get forecasts ready for evaluation
        pending = self.db.query(ForecastTracking).filter(
            ForecastTracking.actual_price.is_(None),
            ForecastTracking.forecast_date <= today
        ).all()

        for forecast in pending:
            # Check if quarter has ended
            target_date = self._get_quarter_end(forecast.forecast_date, int(forecast.quarter[1]))
            if today >= target_date:
                await self._evaluate_single_forecast(forecast, target_date)

    async def _evaluate_single_forecast(
        self,
        forecast: ForecastTracking,
        target_date: date
    ):
        """Evaluate a single forecast against actual price"""
        # Fetch actual price on target date
        actual_price = await self._get_price_on_date(forecast.symbol, target_date)
        if not actual_price:
            return  # Wait for data

        # Calculate errors for each scenario
        errors = {
            'pessimistic': abs(float(actual_price) - float(forecast.pessimistic_price)) / float(actual_price) * 100,
            'realistic': abs(float(actual_price) - float(forecast.realistic_price)) / float(actual_price) * 100,
            'optimistic': abs(float(actual_price) - float(forecast.optimistic_price)) / float(actual_price) * 100
        }

        # Find closest scenario
        closest = min(errors.items(), key=lambda x: x[1])

        # Update tracking record
        forecast.actual_price = actual_price
        forecast.actual_date = target_date
        forecast.closest_scenario = closest[0]
        forecast.accuracy_percentage = 100 - closest[1]  # Accuracy = 100 - error
        forecast.realistic_error_percentage = errors['realistic']
        forecast.evaluated_at = datetime.utcnow()

        self.db.commit()

    async def get_accuracy_stats(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get forecast accuracy statistics"""
        query = self.db.query(ForecastTracking).filter(
            ForecastTracking.actual_price.isnot(None)
        )

        if symbol:
            query = query.filter(ForecastTracking.symbol == symbol)

        forecasts = query.all()

        if not forecasts:
            return {
                'total_forecasts': 0,
                'average_accuracy': 0,
                'realistic_accuracy': 0,
                'scenario_distribution': {}
            }

        # Calculate statistics
        scenario_counts = {'pessimistic': 0, 'realistic': 0, 'optimistic': 0}
        total_accuracy = 0
        total_realistic_error = 0

        for f in forecasts:
            scenario_counts[f.closest_scenario] += 1
            total_accuracy += f.accuracy_percentage
            total_realistic_error += abs(f.realistic_error_percentage)

        return {
            'total_forecasts': len(forecasts),
            'average_accuracy': round(total_accuracy / len(forecasts), 2),
            'realistic_accuracy': round(100 - (total_realistic_error / len(forecasts)), 2),
            'scenario_distribution': {
                k: round(v / len(forecasts) * 100, 1)
                for k, v in scenario_counts.items()
            }
        }

    def _get_quarter_end(self, start_date: date, quarter_offset: int) -> date:
        """Calculate end date of quarter N from start date"""
        # Simple implementation: 3 months per quarter
        end_month = start_date.month + (quarter_offset * 3)
        end_year = start_date.year + (end_month - 1) // 12
        end_month = ((end_month - 1) % 12) + 1

        # Last day of that month
        import calendar
        last_day = calendar.monthrange(end_year, end_month)[1]
        return date(end_year, end_month, last_day)

    async def _get_price_on_date(self, symbol: str, target_date: date) -> Optional[Decimal]:
        """Fetch historical price on specific date"""
        try:
            ticker = yf.Ticker(symbol)
            # Fetch a week of data around target date to handle weekends
            start = target_date - timedelta(days=7)
            end = target_date + timedelta(days=7)

            hist = ticker.history(start=start, end=end)

            # Find closest date
            closest_date = min(hist.index, key=lambda d: abs((d.date() - target_date).days))
            return Decimal(str(hist.loc[closest_date]['Close']))
        except:
            return None
```

**API Endpoints**:
```python
@router.get("/api/analysis/forecast-accuracy", response_model=AccuracyStatsResponse)
async def get_forecast_accuracy(
    symbol: Optional[str] = Query(None),
    tracking_service: ForecastTrackingService = Depends(get_tracking_service)
):
    """
    Get forecast accuracy statistics

    Returns overall accuracy metrics and scenario distribution.
    """
    stats = await tracking_service.get_accuracy_stats(symbol)
    return AccuracyStatsResponse(**stats)

class AccuracyStatsResponse(BaseModel):
    total_forecasts: int
    average_accuracy: float = Field(..., description="Average accuracy percentage")
    realistic_accuracy: float = Field(..., description="Accuracy of realistic scenarios")
    scenario_distribution: Dict[str, float] = Field(
        ...,
        description="Percentage of times each scenario was closest"
    )
```

**Definition of Done**:
- [x] Database schema for forecast tracking
- [x] Forecast recording on generation
- [x] Automated evaluation job (daily)
- [x] Accuracy calculation logic
- [x] Statistics API endpoint
- [x] Historical price fetching
- [x] Unit tests (≥85% coverage)
- [x] Integration tests
- [x] Documentation

**Story Points**: 5
**Priority**: Should Have (Nice to have for MVP, critical for long-term)
**Dependencies**: F8.5-001 (Forecast API)
**Risk Level**: Low
**Assigned To**: Unassigned

---

## Feature 8.6: Analysis UI Dashboard
**Feature Description**: Frontend components for displaying and interacting with AI analysis
**User Value**: Easy access to insights with beautiful, intuitive interface
**Priority**: High
**Complexity**: 8 story points

### Story F8.6-001: Analysis Dashboard Tab
**Status**: 🔴 Not Started
**User Story**: As FX, I want a dedicated Analysis tab so that I can easily access all AI insights

**Acceptance Criteria**:
- **Given** I navigate to the Analysis tab
- **When** the page loads
- **Then** I see global market analysis card
- **And** I see a list of my positions with analysis buttons
- **And** I can click any position to view detailed analysis
- **And** I can request forecast for any position
- **And** loading states are shown during generation
- **And** cached indicators show when analysis is from cache
- **And** I can force refresh any analysis

**Component Structure**:
```typescript
// frontend/src/pages/Analysis.tsx

import React from 'react';
import { GlobalAnalysisCard } from '../components/GlobalAnalysisCard';
import { PositionAnalysisList } from '../components/PositionAnalysisList';
import { ForecastPanel } from '../components/ForecastPanel';

export const AnalysisPage: React.FC = () => {
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'analysis' | 'forecast'>('analysis');

  return (
    <div className="analysis-page">
      <header>
        <h1>Portfolio Analysis</h1>
        <p className="subtitle">AI-powered insights from Claude</p>
      </header>

      <div className="analysis-grid">
        {/* Global Analysis - Full Width */}
        <section className="global-section">
          <GlobalAnalysisCard />
        </section>

        {/* Position List - Left Side */}
        <section className="positions-section">
          <PositionAnalysisList
            onSelectPosition={setSelectedSymbol}
            selectedSymbol={selectedSymbol}
          />
        </section>

        {/* Detail Panel - Right Side */}
        <section className="detail-section">
          {selectedSymbol && (
            <div className="mode-tabs">
              <button
                className={viewMode === 'analysis' ? 'active' : ''}
                onClick={() => setViewMode('analysis')}
              >
                Analysis
              </button>
              <button
                className={viewMode === 'forecast' ? 'active' : ''}
                onClick={() => setViewMode('forecast')}
              >
                Forecast
              </button>
            </div>
          )}

          {selectedSymbol && viewMode === 'analysis' && (
            <PositionAnalysisCard symbol={selectedSymbol} />
          )}

          {selectedSymbol && viewMode === 'forecast' && (
            <ForecastPanel symbol={selectedSymbol} />
          )}

          {!selectedSymbol && (
            <div className="empty-state">
              <p>Select a position to view detailed analysis</p>
            </div>
          )}
        </section>
      </div>
    </div>
  );
};
```

**GlobalAnalysisCard Component**:
```typescript
// frontend/src/components/GlobalAnalysisCard.tsx

import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { analysisApi } from '../api/analysis';

export const GlobalAnalysisCard: React.FC = () => {
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAnalysis = async (forceRefresh = false) => {
    setLoading(true);
    setError(null);
    try {
      const result = await analysisApi.getGlobalAnalysis(forceRefresh);
      setAnalysis(result);
    } catch (err) {
      setError('Failed to load analysis');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalysis();
  }, []);

  if (loading) {
    return <div className="loading-card">Generating market analysis...</div>;
  }

  if (error) {
    return <div className="error-card">{error}</div>;
  }

  return (
    <div className="global-analysis-card">
      <div className="card-header">
        <h2>Market Overview</h2>
        <div className="card-actions">
          {analysis?.cached && (
            <span className="cache-badge">Cached</span>
          )}
          <span className="timestamp">
            {new Date(analysis.generated_at).toLocaleString()}
          </span>
          <button
            onClick={() => loadAnalysis(true)}
            className="refresh-btn"
            title="Generate new analysis"
          >
            Refresh
          </button>
        </div>
      </div>

      <div className="card-body">
        <ReactMarkdown>{analysis.analysis}</ReactMarkdown>
      </div>

      <div className="card-footer">
        <span className="token-count">
          {analysis.tokens_used} tokens
        </span>
      </div>
    </div>
  );
};
```

**PositionAnalysisList Component**:
```typescript
// frontend/src/components/PositionAnalysisList.tsx

interface PositionAnalysisListProps {
  onSelectPosition: (symbol: string) => void;
  selectedSymbol: string | null;
}

export const PositionAnalysisList: React.FC<PositionAnalysisListProps> = ({
  onSelectPosition,
  selectedSymbol
}) => {
  const [positions, setPositions] = useState<any[]>([]);

  useEffect(() => {
    // Fetch positions from portfolio API
    portfolioApi.getPositions().then(setPositions);
  }, []);

  return (
    <div className="position-list">
      <h3>Your Positions</h3>
      <div className="position-items">
        {positions.map(position => (
          <div
            key={position.symbol}
            className={`position-item ${selectedSymbol === position.symbol ? 'selected' : ''}`}
            onClick={() => onSelectPosition(position.symbol)}
          >
            <div className="position-symbol">{position.symbol}</div>
            <div className="position-value">
              €{position.current_value.toFixed(2)}
            </div>
            <div className={`position-pnl ${position.unrealized_pnl >= 0 ? 'positive' : 'negative'}`}>
              {position.unrealized_pnl >= 0 ? '+' : ''}
              {position.unrealized_pnl_percentage.toFixed(2)}%
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
```

**Definition of Done**:
- [x] Analysis page component
- [x] Global analysis card with markdown rendering
- [x] Position list component
- [x] Tab navigation (Analysis/Forecast)
- [x] Loading states
- [x] Error handling
- [x] Cache indicators
- [x] Refresh functionality
- [x] Responsive design
- [x] Unit tests (≥85% coverage)
- [x] Integration tests with mock API

**Story Points**: 5
**Priority**: Must Have
**Dependencies**: F8.3-001 (Global Analysis API)
**Risk Level**: Low
**Assigned To**: Unassigned

---

### Story F8.6-002: Forecast Visualization
**Status**: 🔴 Not Started
**User Story**: As FX, I want to visualize forecasts with charts so that I can easily understand the scenarios

**Acceptance Criteria**:
- **Given** I view a forecast
- **When** the forecast loads
- **Then** I see a chart showing current price and scenarios
- **And** pessimistic/realistic/optimistic scenarios are color-coded
- **And** confidence levels are displayed for each scenario
- **And** assumptions and risks are shown in expandable sections
- **And** I can toggle between Q1 and Q2 views
- **And** overall outlook is prominently displayed

**Forecast Panel Component**:
```typescript
// frontend/src/components/ForecastPanel.tsx

import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { analysisApi } from '../api/analysis';

interface ForecastPanelProps {
  symbol: string;
}

export const ForecastPanel: React.FC<ForecastPanelProps> = ({ symbol }) => {
  const [forecast, setForecast] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [quarter, setQuarter] = useState<'q1' | 'q2'>('q1');

  const loadForecast = async (forceRefresh = false) => {
    setLoading(true);
    try {
      const result = await analysisApi.getForecast(symbol, forceRefresh);
      setForecast(result);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadForecast();
  }, [symbol]);

  if (loading) {
    return <div className="loading">Generating forecast...</div>;
  }

  const quarterData = forecast[`${quarter}_forecast`];

  // Prepare chart data
  const chartData = [
    {
      name: 'Current',
      price: parseFloat(forecast.current_price),
      fill: '#888'
    },
    {
      name: 'Pessimistic',
      price: parseFloat(quarterData.pessimistic.price),
      confidence: quarterData.pessimistic.confidence,
      fill: '#ef4444'
    },
    {
      name: 'Realistic',
      price: parseFloat(quarterData.realistic.price),
      confidence: quarterData.realistic.confidence,
      fill: '#3b82f6'
    },
    {
      name: 'Optimistic',
      price: parseFloat(quarterData.optimistic.price),
      confidence: quarterData.optimistic.confidence,
      fill: '#22c55e'
    }
  ];

  return (
    <div className="forecast-panel">
      <div className="panel-header">
        <h3>Forecast for {symbol}</h3>
        <div className="quarter-toggle">
          <button
            className={quarter === 'q1' ? 'active' : ''}
            onClick={() => setQuarter('q1')}
          >
            Q1
          </button>
          <button
            className={quarter === 'q2' ? 'active' : ''}
            onClick={() => setQuarter('q2')}
          >
            Q2
          </button>
        </div>
      </div>

      <div className="outlook-box">
        <h4>Overall Outlook</h4>
        <p>{forecast.overall_outlook}</p>
      </div>

      <div className="forecast-chart">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="price" fill="#8884d8" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="scenarios">
        {['pessimistic', 'realistic', 'optimistic'].map(scenario => (
          <ScenarioCard
            key={scenario}
            scenario={scenario}
            data={quarterData[scenario]}
          />
        ))}
      </div>
    </div>
  );
};

const ScenarioCard: React.FC<{ scenario: string; data: any }> = ({ scenario, data }) => {
  const [expanded, setExpanded] = useState(false);

  const colors = {
    pessimistic: '#ef4444',
    realistic: '#3b82f6',
    optimistic: '#22c55e'
  };

  return (
    <div className="scenario-card" style={{ borderLeftColor: colors[scenario] }}>
      <div className="scenario-header" onClick={() => setExpanded(!expanded)}>
        <h4>{scenario.charAt(0).toUpperCase() + scenario.slice(1)}</h4>
        <div className="scenario-price">€{parseFloat(data.price).toFixed(2)}</div>
        <div className="scenario-confidence">{data.confidence}% confidence</div>
      </div>

      {expanded && (
        <div className="scenario-details">
          <div className="detail-section">
            <h5>Assumptions</h5>
            <p>{data.assumptions}</p>
          </div>
          <div className="detail-section">
            <h5>Risks</h5>
            <p>{data.risks}</p>
          </div>
        </div>
      )}
    </div>
  );
};
```

**Styling**:
```css
/* frontend/src/components/ForecastPanel.css */

.forecast-panel {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.quarter-toggle button {
  padding: 8px 16px;
  border: 1px solid #ddd;
  background: white;
  cursor: pointer;
}

.quarter-toggle button.active {
  background: #3b82f6;
  color: white;
}

.outlook-box {
  background: #f8fafc;
  padding: 16px;
  border-radius: 6px;
  margin-bottom: 20px;
}

.scenarios {
  display: grid;
  gap: 12px;
  margin-top: 20px;
}

.scenario-card {
  border-left: 4px solid;
  padding: 16px;
  background: #fafafa;
  cursor: pointer;
  transition: all 0.2s;
}

.scenario-card:hover {
  background: #f5f5f5;
}

.scenario-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.scenario-price {
  font-size: 1.5rem;
  font-weight: bold;
}

.scenario-confidence {
  font-size: 0.9rem;
  color: #666;
}

.scenario-details {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #ddd;
}

.detail-section {
  margin-bottom: 12px;
}

.detail-section h5 {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 4px;
}
```

**Definition of Done**:
- [x] Forecast panel component
- [x] Bar chart visualization
- [x] Quarter toggle (Q1/Q2)
- [x] Scenario cards with expand/collapse
- [x] Color coding for scenarios
- [x] Confidence display
- [x] Assumptions and risks sections
- [x] Responsive design
- [x] Loading states
- [x] Unit tests (≥85% coverage)
- [x] Integration tests

**Story Points**: 5
**Priority**: Must Have
**Dependencies**: F8.5-001 (Forecast API)
**Risk Level**: Low
**Assigned To**: Unassigned

---

## Technical Design Notes

### Architecture Overview
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

### Data Flow
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

### Token Management
- **Budget**: Tier 1 Anthropic allows 50 req/min, ~4M tokens/day
- **Typical usage**:
  - Global analysis: ~1,500 tokens
  - Position analysis: ~800 tokens
  - Forecast: ~2,000 tokens
- **Daily estimate** (10 positions, 2 analyses/day each):
  - 1 global × 1,500 = 1,500
  - 10 positions × 800 × 2 = 16,000
  - 5 forecasts × 2,000 = 10,000
  - **Total**: ~27,500 tokens/day (well within limits)

### Caching Strategy
| Analysis Type | Cache TTL | Justification |
|---------------|-----------|---------------|
| Global | 1 hour | Market conditions change frequently |
| Position | 1 hour | Position-specific news updates often |
| Forecast | 24 hours | Forecasts are longer-term, expensive to generate |

### Error Handling
- **API failures**: Retry with exponential backoff (3 attempts)
- **Rate limits**: Queue requests and delay
- **Parsing errors**: Log and return graceful error message
- **Timeout**: 30-second timeout, inform user to try again

---

## Dependencies
- **External**:
  - Anthropic Claude API (anthropic Python SDK)
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

## Testing Strategy

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

3. **Manual Testing**:
   - Anthropic API with real requests (limited)
   - UI/UX validation
   - Forecast accuracy after quarters complete

4. **Performance Tests**:
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
- [x] All 14 stories completed
- [x] Database schema for prompts and analysis results
- [x] Anthropic Claude integration working
- [x] Global, position, and forecast analysis functional
- [x] Frontend UI for viewing all analysis types
- [x] Caching system reducing API costs
- [x] Forecast accuracy tracking implemented
- [x] Unit test coverage ≥85% (mandatory)
- [x] Integration tests passing
- [x] API documentation complete
- [x] Performance benchmarks met
- [x] User acceptance: FX approves analysis quality

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
