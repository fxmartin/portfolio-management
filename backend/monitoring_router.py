# ABOUTME: Monitoring endpoints for system health and provider statistics
# ABOUTME: Tracks market data provider performance and API usage

from fastapi import APIRouter, HTTPException
from typing import Dict
import os
from datetime import datetime

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


# Global aggregator instance for tracking statistics
# This will be set by the application when initialized
_global_aggregator = None


def set_global_aggregator(aggregator):
    """Set the global aggregator instance for monitoring"""
    global _global_aggregator
    _global_aggregator = aggregator


@router.get("/market-data")
async def get_market_data_stats() -> Dict:
    """
    Get comprehensive market data provider statistics

    Returns:
        Dictionary with:
        - providers: Success/failure counts for each provider
        - circuit_breakers: Circuit breaker status (open/closed, failures)
        - alpha_vantage: API usage stats (calls today, daily limit, usage %)
        - yahoo_finance: Success rate percentage
        - configuration: API key status and rate limits
    """
    try:
        # Get Alpha Vantage configuration
        alpha_vantage_api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        alpha_vantage_rate_limit_per_minute = int(os.getenv("ALPHA_VANTAGE_RATE_LIMIT_PER_MINUTE", "5"))
        alpha_vantage_rate_limit_per_day = int(os.getenv("ALPHA_VANTAGE_RATE_LIMIT_PER_DAY", "100"))

        # Configuration status
        configuration = {
            "alpha_vantage_configured": bool(alpha_vantage_api_key),
            "alpha_vantage_rate_limit_per_minute": alpha_vantage_rate_limit_per_minute,
            "alpha_vantage_rate_limit_per_day": alpha_vantage_rate_limit_per_day,
        }

        # If aggregator is available, get stats
        if _global_aggregator:
            stats = _global_aggregator.get_provider_stats()

            # Calculate usage percentages
            from market_data_aggregator import DataProvider

            av_stats = stats['stats'][DataProvider.ALPHA_VANTAGE]
            total_av_calls = av_stats['success'] + av_stats['failure']

            yahoo_stats = stats['stats'][DataProvider.YAHOO_FINANCE]
            total_yahoo_calls = yahoo_stats['success'] + yahoo_stats['failure']
            yahoo_success_rate = (
                (yahoo_stats['success'] / total_yahoo_calls * 100)
                if total_yahoo_calls > 0 else 100.0
            )

            return {
                "providers": stats['stats'],
                "circuit_breakers": stats['circuit_breakers'],
                "alpha_vantage": {
                    "calls_today": total_av_calls,
                    "daily_limit": alpha_vantage_rate_limit_per_day,
                    "usage_percent": (
                        (total_av_calls / alpha_vantage_rate_limit_per_day) * 100
                        if alpha_vantage_rate_limit_per_day > 0 else 0
                    ),
                    "rate_limited": total_av_calls >= alpha_vantage_rate_limit_per_day,
                    "at_80_percent_threshold": total_av_calls >= (alpha_vantage_rate_limit_per_day * 0.8)
                },
                "yahoo_finance": {
                    "success_rate": yahoo_success_rate,
                    "total_calls": total_yahoo_calls
                },
                "configuration": configuration,
                "last_updated": datetime.now().isoformat()
            }
        else:
            # No aggregator available yet (application still starting up)
            return {
                "providers": {},
                "circuit_breakers": {},
                "alpha_vantage": {
                    "calls_today": 0,
                    "daily_limit": alpha_vantage_rate_limit_per_day,
                    "usage_percent": 0,
                    "rate_limited": False,
                    "at_80_percent_threshold": False
                },
                "yahoo_finance": {
                    "success_rate": 100.0,
                    "total_calls": 0
                },
                "configuration": configuration,
                "last_updated": datetime.now().isoformat(),
                "note": "Aggregator not initialized yet - stats will be available after first market data fetch"
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch market data statistics: {str(e)}"
        )


@router.get("/health")
async def health_check() -> Dict:
    """
    Basic health check endpoint

    Returns:
        Dictionary with status and timestamp
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": "connected",  # TODO: Add actual DB health check
            "market_data_aggregator": "available" if _global_aggregator else "not_initialized"
        }
    }
