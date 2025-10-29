# ABOUTME: Claude API service for generating market analysis using Anthropic Claude
# ABOUTME: Handles rate limiting, retries, token tracking, and error management

from anthropic import AsyncAnthropic
from typing import Optional, Dict, Any
import asyncio
import time
from collections import deque
import logging

try:
    from .config import Settings
except ImportError:
    from config import Settings

# Configure logging
logger = logging.getLogger(__name__)


# Custom exceptions
class ClaudeAPIError(Exception):
    """Base exception for Claude API errors."""
    pass


class RateLimitError(ClaudeAPIError):
    """Rate limit exceeded."""
    pass


class InvalidResponseError(ClaudeAPIError):
    """Response format invalid."""
    pass


class ClaudeService:
    """
    Service for interacting with Anthropic Claude API.

    Features:
    - Async API calls
    - Rate limiting (50 requests/minute by default)
    - Automatic retries with exponential backoff
    - Token usage tracking
    - Comprehensive error handling
    """

    def __init__(self, config: Settings):
        """
        Initialize Claude service with configuration.

        Args:
            config: Settings object with Anthropic configuration
        """
        self.client = AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
        self.model = config.ANTHROPIC_MODEL
        self.max_tokens = config.ANTHROPIC_MAX_TOKENS
        self.temperature = config.ANTHROPIC_TEMPERATURE
        self.timeout = config.ANTHROPIC_TIMEOUT
        self.max_retries = config.ANTHROPIC_MAX_RETRIES

        # Rate limiting
        self.rate_limit = config.ANTHROPIC_RATE_LIMIT
        self.request_times = deque(maxlen=self.rate_limit)

        logger.info(
            f"Initialized ClaudeService with model={self.model}, "
            f"rate_limit={self.rate_limit} req/min"
        )

    async def generate_analysis(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate analysis using Claude API.

        Args:
            prompt: User prompt to send to Claude
            system_prompt: Optional system prompt (uses default if not provided)
            temperature: Optional temperature override (0-1)
            max_tokens: Optional max tokens override

        Returns:
            {
                'content': str,  # Analysis text
                'tokens_used': int,  # Total tokens (input + output)
                'model': str,  # Model used
                'generation_time_ms': int,  # Time taken
                'stop_reason': str  # Reason for stopping
            }

        Raises:
            ClaudeAPIError: On API errors
            RateLimitError: On rate limit errors
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

                result = {
                    'content': response.content[0].text,
                    'tokens_used': response.usage.input_tokens + response.usage.output_tokens,
                    'model': response.model,
                    'generation_time_ms': int((end_time - start_time) * 1000),
                    'stop_reason': response.stop_reason
                }

                logger.info(
                    f"Generated analysis: {result['tokens_used']} tokens, "
                    f"{result['generation_time_ms']}ms"
                )

                return result

            except Exception as e:
                logger.warning(f"API call failed (attempt {attempt + 1}/{self.max_retries}): {e}")

                # Check if it's a rate limit error
                if hasattr(e, '__class__') and 'RateLimitError' in e.__class__.__name__:
                    if attempt == self.max_retries - 1:
                        raise RateLimitError("Rate limit exceeded, try again later")

                # Check if it's a timeout error
                if hasattr(e, '__class__') and 'TimeoutError' in e.__class__.__name__:
                    if attempt == self.max_retries - 1:
                        raise ClaudeAPIError(f"Request timeout: {e}")

                # Last attempt, raise the error
                if attempt == self.max_retries - 1:
                    logger.error(f"Claude API error after {self.max_retries} attempts: {e}")
                    raise ClaudeAPIError(f"Analysis generation failed: {e}")

                # Exponential backoff: 1s, 2s, 4s
                wait_time = 2 ** attempt
                logger.debug(f"Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)

        raise Exception("Max retries exceeded")

    async def _check_rate_limit(self):
        """
        Ensure we don't exceed rate limits.

        Tracks request times and delays if necessary to stay within limit.
        """
        now = time.time()

        # Remove requests older than 1 minute
        while self.request_times and now - self.request_times[0] > 60:
            self.request_times.popleft()

        # If at limit, wait
        if len(self.request_times) >= self.rate_limit:
            sleep_time = 60 - (now - self.request_times[0])
            if sleep_time > 0:
                logger.warning(f"Rate limit reached, waiting {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)

        self.request_times.append(now)

    def _default_system_prompt(self) -> str:
        """
        Get default system prompt for financial analysis.

        Returns:
            System prompt string
        """
        return """You are a professional financial analyst providing market insights for a portfolio management application.

Your analysis should be:
- Data-driven and factual
- Concise and actionable
- Focused on the specific portfolio context provided
- Free from disclaimers (user understands this is AI analysis)
- Formatted in clear, readable markdown

Avoid generic advice. Focus on specific insights relevant to the user's holdings."""
