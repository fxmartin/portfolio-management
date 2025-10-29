# ABOUTME: Unit tests for ClaudeService - Anthropic Claude API integration
# ABOUTME: Tests rate limiting, retries, token tracking, and error handling with mocked API

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
import asyncio
from collections import namedtuple

# Create mock Anthropic types
MockUsage = namedtuple('Usage', ['input_tokens', 'output_tokens'])
MockContent = namedtuple('Content', ['text'])
MockMessage = namedtuple('Message', ['content', 'usage', 'model', 'stop_reason'])


class TestClaudeServiceInitialization:
    """Test ClaudeService initialization and configuration."""

    @pytest.mark.asyncio
    async def test_init_with_config(self):
        """Test service initializes with correct configuration."""
        from config import Settings
        from claude_service import ClaudeService

        # Create test config
        config = Settings(
            ANTHROPIC_API_KEY="test-key",
            ANTHROPIC_MODEL="claude-sonnet-4-5-20250929",
            ANTHROPIC_MAX_TOKENS=4096,
            ANTHROPIC_TEMPERATURE=0.3,
            ANTHROPIC_TIMEOUT=30,
            ANTHROPIC_MAX_RETRIES=3,
            ANTHROPIC_RATE_LIMIT=50,
            DATABASE_URL="postgresql://test:test@localhost/test",
            POSTGRES_PASSWORD="test"
        )

        service = ClaudeService(config)

        assert service.model == "claude-sonnet-4-5-20250929"
        assert service.max_tokens == 4096
        assert service.temperature == 0.3
        assert service.timeout == 30
        assert service.max_retries == 3
        assert service.rate_limit == 50

    @pytest.mark.asyncio
    async def test_init_creates_async_client(self):
        """Test that service creates AsyncAnthropic client."""
        from config import Settings
        from claude_service import ClaudeService

        config = Settings(
            ANTHROPIC_API_KEY="test-key",
            DATABASE_URL="postgresql://test:test@localhost/test",
            POSTGRES_PASSWORD="test"
        )

        service = ClaudeService(config)
        assert service.client is not None


class TestClaudeServiceAnalysisGeneration:
    """Test analysis generation with Claude API."""

    @pytest.mark.asyncio
    async def test_generate_analysis_success(self):
        """Test successful analysis generation."""
        from config import Settings
        from claude_service import ClaudeService

        config = Settings(
            ANTHROPIC_API_KEY="test-key",
            DATABASE_URL="postgresql://test:test@localhost/test",
            POSTGRES_PASSWORD="test"
        )

        service = ClaudeService(config)

        # Mock the API response
        mock_response = MockMessage(
            content=[MockContent(text="This is a test analysis.")],
            usage=MockUsage(input_tokens=100, output_tokens=50),
            model="claude-sonnet-4-5-20250929",
            stop_reason="end_turn"
        )

        with patch.object(service.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            result = await service.generate_analysis("Test prompt")

            # Verify result structure
            assert result['content'] == "This is a test analysis."
            assert result['tokens_used'] == 150  # 100 + 50
            assert result['model'] == "claude-sonnet-4-5-20250929"
            assert result['stop_reason'] == "end_turn"
            assert 'generation_time_ms' in result

    @pytest.mark.asyncio
    async def test_generate_analysis_with_custom_temperature(self):
        """Test analysis generation with custom temperature."""
        from config import Settings
        from claude_service import ClaudeService

        config = Settings(
            ANTHROPIC_API_KEY="test-key",
            DATABASE_URL="postgresql://test:test@localhost/test",
            POSTGRES_PASSWORD="test"
        )

        service = ClaudeService(config)

        mock_response = MockMessage(
            content=[MockContent(text="Test")],
            usage=MockUsage(input_tokens=10, output_tokens=5),
            model="claude-sonnet-4-5-20250929",
            stop_reason="end_turn"
        )

        with patch.object(service.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            await service.generate_analysis("Test prompt", temperature=0.1)

            # Verify custom temperature was used
            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs['temperature'] == 0.1

    @pytest.mark.asyncio
    async def test_generate_analysis_with_custom_system_prompt(self):
        """Test analysis generation with custom system prompt."""
        from config import Settings
        from claude_service import ClaudeService

        config = Settings(
            ANTHROPIC_API_KEY="test-key",
            DATABASE_URL="postgresql://test:test@localhost/test",
            POSTGRES_PASSWORD="test"
        )

        service = ClaudeService(config)

        mock_response = MockMessage(
            content=[MockContent(text="Test")],
            usage=MockUsage(input_tokens=10, output_tokens=5),
            model="claude-sonnet-4-5-20250929",
            stop_reason="end_turn"
        )

        with patch.object(service.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            custom_system = "You are a test assistant."
            await service.generate_analysis("Test prompt", system_prompt=custom_system)

            # Verify custom system prompt was used
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs['system'] == custom_system


class TestClaudeServiceRateLimiting:
    """Test rate limiting functionality."""

    @pytest.mark.asyncio
    async def test_rate_limiting_enforced(self):
        """Test that rate limiting prevents exceeding limits."""
        from config import Settings
        from claude_service import ClaudeService

        config = Settings(
            ANTHROPIC_API_KEY="test-key",
            ANTHROPIC_RATE_LIMIT=5,  # Very low limit for testing
            DATABASE_URL="postgresql://test:test@localhost/test",
            POSTGRES_PASSWORD="test"
        )

        service = ClaudeService(config)

        # Mock successful responses
        mock_response = MockMessage(
            content=[MockContent(text="Test")],
            usage=MockUsage(input_tokens=10, output_tokens=5),
            model="claude-sonnet-4-5-20250929",
            stop_reason="end_turn"
        )

        with patch.object(service.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            # Make 5 rapid requests (at limit)
            start_time = asyncio.get_event_loop().time()
            for _ in range(5):
                await service.generate_analysis("Test")
            elapsed = asyncio.get_event_loop().time() - start_time

            # Should complete quickly (not rate limited)
            assert elapsed < 1.0

            # 6th request should be rate limited
            start_time = asyncio.get_event_loop().time()
            await service.generate_analysis("Test")
            elapsed = asyncio.get_event_loop().time() - start_time

            # Should have been delayed
            assert elapsed >= 0.1  # At least some delay

    @pytest.mark.asyncio
    async def test_rate_limit_tracking(self):
        """Test that rate limit tracking works correctly."""
        from config import Settings
        from claude_service import ClaudeService

        config = Settings(
            ANTHROPIC_API_KEY="test-key",
            ANTHROPIC_RATE_LIMIT=10,
            DATABASE_URL="postgresql://test:test@localhost/test",
            POSTGRES_PASSWORD="test"
        )

        service = ClaudeService(config)

        # Initially no requests tracked
        assert len(service.request_times) == 0

        # Make a mock request
        mock_response = MockMessage(
            content=[MockContent(text="Test")],
            usage=MockUsage(input_tokens=10, output_tokens=5),
            model="claude-sonnet-4-5-20250929",
            stop_reason="end_turn"
        )

        with patch.object(service.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            await service.generate_analysis("Test")

        # Should have 1 request tracked
        assert len(service.request_times) == 1


class TestClaudeServiceRetryLogic:
    """Test retry logic with exponential backoff."""

    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """Test that service retries on API failure."""
        from config import Settings
        from claude_service import ClaudeService, ClaudeAPIError

        config = Settings(
            ANTHROPIC_API_KEY="test-key",
            ANTHROPIC_MAX_RETRIES=3,
            DATABASE_URL="postgresql://test:test@localhost/test",
            POSTGRES_PASSWORD="test"
        )

        service = ClaudeService(config)

        # Mock first 2 calls fail, 3rd succeeds
        mock_response = MockMessage(
            content=[MockContent(text="Success")],
            usage=MockUsage(input_tokens=10, output_tokens=5),
            model="claude-sonnet-4-5-20250929",
            stop_reason="end_turn"
        )

        call_count = 0
        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("API Error")
            return mock_response

        with patch.object(service.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = side_effect

            result = await service.generate_analysis("Test")

            # Should have succeeded on 3rd try
            assert call_count == 3
            assert result['content'] == "Success"

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test that service fails after max retries."""
        from config import Settings
        from claude_service import ClaudeService, ClaudeAPIError

        config = Settings(
            ANTHROPIC_API_KEY="test-key",
            ANTHROPIC_MAX_RETRIES=2,
            DATABASE_URL="postgresql://test:test@localhost/test",
            POSTGRES_PASSWORD="test"
        )

        service = ClaudeService(config)

        with patch.object(service.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API Error")

            with pytest.raises(Exception):
                await service.generate_analysis("Test")

            # Should have tried max_retries times
            assert mock_create.call_count == 2

    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self):
        """Test that exponential backoff increases wait time."""
        from config import Settings
        from claude_service import ClaudeService

        config = Settings(
            ANTHROPIC_API_KEY="test-key",
            ANTHROPIC_MAX_RETRIES=3,
            DATABASE_URL="postgresql://test:test@localhost/test",
            POSTGRES_PASSWORD="test"
        )

        service = ClaudeService(config)

        with patch.object(service.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API Error")

            start_time = asyncio.get_event_loop().time()

            with pytest.raises(Exception):
                await service.generate_analysis("Test")

            elapsed = asyncio.get_event_loop().time() - start_time

            # Should have waited: 1s + 2s = 3s (exponential: 2^0, 2^1)
            assert elapsed >= 3.0


class TestClaudeServiceErrorHandling:
    """Test error handling for various API errors."""

    @pytest.mark.asyncio
    async def test_api_timeout_error(self):
        """Test handling of API timeout errors."""
        from config import Settings
        from claude_service import ClaudeService, ClaudeAPIError
        from anthropic import APITimeoutError

        config = Settings(
            ANTHROPIC_API_KEY="test-key",
            ANTHROPIC_MAX_RETRIES=1,
            DATABASE_URL="postgresql://test:test@localhost/test",
            POSTGRES_PASSWORD="test"
        )

        service = ClaudeService(config)

        with patch.object(service.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = APITimeoutError("Timeout")

            with pytest.raises(ClaudeAPIError) as exc_info:
                await service.generate_analysis("Test")

            assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_rate_limit_error(self):
        """Test handling of rate limit errors."""
        from config import Settings
        from claude_service import ClaudeService, RateLimitError

        config = Settings(
            ANTHROPIC_API_KEY="test-key",
            ANTHROPIC_MAX_RETRIES=1,
            DATABASE_URL="postgresql://test:test@localhost/test",
            POSTGRES_PASSWORD="test"
        )

        service = ClaudeService(config)

        # Create a simple exception that has RateLimitError in the class name
        class MockRateLimitError(Exception):
            pass
        MockRateLimitError.__name__ = "RateLimitError"

        with patch.object(service.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = MockRateLimitError("Rate limit exceeded")

            with pytest.raises(RateLimitError) as exc_info:
                await service.generate_analysis("Test")

            assert "rate limit" in str(exc_info.value).lower()


class TestClaudeServiceSystemPrompt:
    """Test default system prompt functionality."""

    @pytest.mark.asyncio
    async def test_default_system_prompt_used(self):
        """Test that default system prompt is used when none provided."""
        from config import Settings
        from claude_service import ClaudeService

        config = Settings(
            ANTHROPIC_API_KEY="test-key",
            DATABASE_URL="postgresql://test:test@localhost/test",
            POSTGRES_PASSWORD="test"
        )

        service = ClaudeService(config)

        mock_response = MockMessage(
            content=[MockContent(text="Test")],
            usage=MockUsage(input_tokens=10, output_tokens=5),
            model="claude-sonnet-4-5-20250929",
            stop_reason="end_turn"
        )

        with patch.object(service.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            await service.generate_analysis("Test prompt")

            call_kwargs = mock_create.call_args.kwargs
            system_prompt = call_kwargs['system']

            # Verify default system prompt contains expected keywords
            assert "financial analyst" in system_prompt.lower()
            assert "portfolio" in system_prompt.lower()

    @pytest.mark.asyncio
    async def test_default_system_prompt_content(self):
        """Test that default system prompt has correct content."""
        from config import Settings
        from claude_service import ClaudeService

        config = Settings(
            ANTHROPIC_API_KEY="test-key",
            DATABASE_URL="postgresql://test:test@localhost/test",
            POSTGRES_PASSWORD="test"
        )

        service = ClaudeService(config)
        system_prompt = service._default_system_prompt()

        # Should contain key instructions
        assert "financial analyst" in system_prompt.lower()
        assert "data-driven" in system_prompt.lower()
        assert "concise" in system_prompt.lower()
        assert "markdown" in system_prompt.lower()
