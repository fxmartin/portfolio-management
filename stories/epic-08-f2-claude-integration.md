## Feature 8.2: Anthropic Claude Integration
**Feature Description**: Core integration with Anthropic Claude API for generating market analysis
**User Value**: Access to state-of-the-art AI analysis of market conditions and portfolio
**Priority**: High (Enables all analysis features)
**Complexity**: 13 story points

### Story F8.2-001: Claude API Client
**Status**: ✅ Complete (Oct 29, 2025)
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
- [x] Anthropic SDK installed and configured ✅
- [x] ClaudeService class with async support ✅
- [x] Rate limiting implementation ✅
- [x] Retry logic with exponential backoff ✅
- [x] Token usage tracking ✅
- [x] Error handling for all API errors ✅
- [x] Environment variable configuration ✅
- [x] Unit tests with mocked API (≥85% coverage) ✅ 97% coverage
- [x] Integration test with real API (manual) ✅ 787 tokens tested
- [x] Logging for debugging and monitoring ✅

**Implementation Summary** (Oct 29, 2025):
- **Files Created**: `config.py` (51 lines), `claude_service.py` (186 lines), `tests/test_claude_service.py` (442 lines), `tests/manual_claude_integration_test.py` (184 lines)
- **Test Results**: 14/14 tests passing, 97% code coverage
- **Real API Test**: Successfully generated Bitcoin analysis in 4.9s using 787 tokens across 4 calls
- **Dependencies**: `anthropic>=0.72.0`, `pydantic-settings>=2.11.0`, `python-dotenv>=1.2.1`

**Story Points**: 8
**Priority**: Must Have
**Dependencies**: None (foundation)
**Risk Level**: Medium (external API dependency)
**Assigned To**: Unassigned

---

### Story F8.2-002: Analysis Service Layer
**Status**: ✅ Complete (Oct 29, 2025)
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
- [x] AnalysisService class implemented ✅
- [x] Global analysis generation ✅
- [x] Position analysis generation ✅
- [x] Forecast generation with JSON parsing ✅
- [x] Cache integration (Redis) ✅
- [x] Database storage of results ✅
- [x] Error handling and validation ✅
- [x] Unit tests (≥85% coverage) ✅ 89% coverage
- [x] Integration tests ✅
- [x] Performance: <10s for global, <5s for position ✅

**Implementation Summary** (Oct 29, 2025):
- **Files Created**: `analysis_service.py` (401 lines), `tests/test_analysis_service.py` (661 lines)
- **Test Results**: 11/11 tests passing, 89% code coverage
- **Key Features**:
  - Three analysis types: global (portfolio-wide), position (per-symbol), forecast (two-quarter scenarios)
  - Smart caching: 1h TTL for analyses, 24h for forecasts
  - Database persistence: All analyses stored in `analysis_results` table
  - Recommendation extraction: HOLD/BUY_MORE/REDUCE/SELL from text
  - JSON fallback: Extracts forecast JSON from markdown code blocks
  - Template integration: Uses PromptRenderer for dynamic prompts

**Story Points**: 5
**Priority**: Must Have
**Dependencies**: F8.1-003 (Template Engine), F8.2-001 (Claude Client)
**Risk Level**: Medium
**Assigned To**: Unassigned

