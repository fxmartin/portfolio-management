# ABOUTME: Redis cache service for analysis results and price data
# ABOUTME: Provides async caching with TTL support for improved performance

"""
Cache Service for Portfolio Management

Provides async Redis caching for:
- Analysis results (1-hour TTL)
- Forecast results (24-hour TTL)
- Price data (15-minute TTL)
"""

import json
import redis.asyncio as redis
from typing import Optional, Any, Dict
from datetime import datetime
import logging
from config import get_settings

logger = logging.getLogger(__name__)


class CacheService:
    """
    Async Redis cache service.

    Handles caching of analysis results, forecasts, and price data
    with configurable TTL values.
    """

    def __init__(self):
        """Initialize Redis connection from environment configuration."""
        settings = get_settings()
        redis_url = settings.REDIS_URL

        # Parse Redis URL
        self.client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        logger.info(f"Initialized CacheService with Redis at {redis_url}")

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached data by key.

        Args:
            key: Cache key to retrieve

        Returns:
            Cached data dictionary or None if not found/expired
        """
        try:
            cached_json = await self.client.get(key)
            if cached_json:
                data = json.loads(cached_json)
                # Convert ISO datetime strings back to datetime objects
                if 'generated_at' in data:
                    data['generated_at'] = datetime.fromisoformat(data['generated_at'])
                logger.debug(f"Cache hit: {key}")
                return data
            logger.debug(f"Cache miss: {key}")
            return None
        except Exception as e:
            logger.error(f"Cache get error for {key}: {e}")
            return None

    async def set(self, key: str, value: Dict[str, Any], ttl: int = 3600):
        """
        Set cached data with TTL.

        Args:
            key: Cache key
            value: Data to cache (must be JSON-serializable)
            ttl: Time-to-live in seconds (default: 1 hour)
        """
        try:
            # Convert datetime objects to ISO strings for JSON serialization
            serializable_value = value.copy()
            if 'generated_at' in serializable_value:
                serializable_value['generated_at'] = serializable_value['generated_at'].isoformat()

            await self.client.set(key, json.dumps(serializable_value), ex=ttl)
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"Cache set error for {key}: {e}")

    async def delete(self, key: str):
        """
        Delete cached data.

        Args:
            key: Cache key to delete
        """
        try:
            await self.client.delete(key)
            logger.debug(f"Cache delete: {key}")
        except Exception as e:
            logger.error(f"Cache delete error for {key}: {e}")

    async def clear_pattern(self, pattern: str):
        """
        Clear all keys matching a pattern.

        Args:
            pattern: Redis key pattern (e.g., "analysis:*")
        """
        try:
            cursor = 0
            keys_deleted = 0

            while True:
                cursor, keys = await self.client.scan(cursor, match=pattern, count=100)
                if keys:
                    await self.client.delete(*keys)
                    keys_deleted += len(keys)
                if cursor == 0:
                    break

            logger.info(f"Cleared {keys_deleted} keys matching pattern: {pattern}")
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")

    async def close(self):
        """Close Redis connection."""
        await self.client.close()
        logger.info("Closed Redis connection")
