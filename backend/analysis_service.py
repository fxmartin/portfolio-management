# ABOUTME: Analysis service orchestrating prompt rendering and Claude API calls
# ABOUTME: Generates global, position-level, and forecast analyses with caching

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import json
import re
import logging
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from .claude_service import ClaudeService
    from .prompt_service import PromptService
    from .prompt_renderer import PromptRenderer, PromptDataCollector
    from .models import AnalysisResult
except ImportError:
    from claude_service import ClaudeService
    from prompt_service import PromptService
    from prompt_renderer import PromptRenderer, PromptDataCollector
    from models import AnalysisResult

# Configure logging
logger = logging.getLogger(__name__)


class AnalysisService:
    """
    Service for generating AI-powered market analysis.

    Orchestrates the complete analysis flow:
    1. Check cache
    2. Fetch prompt template from database
    3. Collect portfolio/market data
    4. Render template with data
    5. Call Claude API
    6. Parse and validate response
    7. Store in database
    8. Cache result
    """

    def __init__(
        self,
        db: AsyncSession,
        claude_service: ClaudeService,
        prompt_service: PromptService,
        data_collector: PromptDataCollector,
        cache_service: Any  # Redis cache service
    ):
        """
        Initialize analysis service.

        Args:
            db: Database session
            claude_service: Claude API service
            prompt_service: Prompt management service
            data_collector: Portfolio data collection service
            cache_service: Redis cache service
        """
        self.db = db
        self.claude = claude_service
        self.prompts = prompt_service
        self.data = data_collector
        self.cache = cache_service

        logger.info("Initialized AnalysisService")

    async def generate_global_analysis(
        self,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Generate global market analysis for entire portfolio.

        Args:
            force_refresh: If True, bypass cache and generate fresh analysis

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
                logger.info("Returning cached global analysis")
                return {**cached, 'cached': True}

        logger.info("Generating fresh global analysis")

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
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        self.db.add(analysis_record)
        await self.db.commit()

        # Cache for 24 hours (reduces API calls by 96%)
        analysis_data = {
            'analysis': result['content'],
            'global_crypto_market': data.get('global_crypto_market'),  # Include global crypto market data
            'market_indicators': data.get('market_indicators'),  # Include global market indicators
            'generated_at': datetime.utcnow(),
            'tokens_used': result['tokens_used']
        }
        await self.cache.set(cache_key, analysis_data, ttl=86400)

        logger.info(f"Global analysis generated: {result['tokens_used']} tokens")

        return {**analysis_data, 'cached': False}

    async def generate_position_analysis(
        self,
        symbol: str,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Generate analysis for specific position.

        Args:
            symbol: Asset symbol (e.g., "BTC", "AAPL")
            force_refresh: If True, bypass cache

        Returns:
            {
                'analysis': str,
                'recommendation': str,  # HOLD, BUY_MORE, REDUCE, SELL
                'generated_at': datetime,
                'tokens_used': int,
                'cached': bool
            }
        """
        cache_key = f"analysis:position:{symbol}"

        if not force_refresh:
            cached = await self._get_cached_analysis(cache_key)
            if cached:
                logger.info(f"Returning cached position analysis for {symbol}")
                return {**cached, 'cached': True}

        logger.info(f"Generating fresh position analysis for {symbol}")

        # Fetch prompt
        prompt_template = await self.prompts.get_prompt_by_name("position_analysis")
        if not prompt_template:
            raise ValueError("Position analysis prompt not found")

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
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        self.db.add(analysis_record)
        await self.db.commit()

        # Extract crypto fundamentals if available
        crypto_fundamentals = None
        if all(key in data for key in ['market_cap', 'market_cap_rank', 'ath', 'atl']):
            crypto_fundamentals = {
                'market_cap': data.get('market_cap'),
                'market_cap_rank': data.get('market_cap_rank'),
                'total_volume_24h': data.get('total_volume_24h'),
                'circulating_supply': data.get('circulating_supply'),
                'max_supply': data.get('max_supply'),
                'ath': data.get('ath'),
                'ath_date': data.get('ath_date'),
                'ath_change_percentage': data.get('ath_change_percentage'),
                'atl': data.get('atl'),
                'atl_date': data.get('atl_date'),
                'atl_change_percentage': data.get('atl_change_percentage'),
                'price_change_percentage_7d': data.get('price_change_percentage_7d'),
                'price_change_percentage_30d': data.get('price_change_percentage_30d'),
                'price_change_percentage_1y': data.get('price_change_percentage_1y'),
                'all_time_roi': data.get('all_time_roi')
            }

        analysis_data = {
            'analysis': result['content'],
            'recommendation': parsed_data.get('recommendation'),
            'crypto_fundamentals': crypto_fundamentals,
            'generated_at': datetime.utcnow(),
            'tokens_used': result['tokens_used']
        }
        await self.cache.set(cache_key, analysis_data, ttl=86400)

        logger.info(
            f"Position analysis generated for {symbol}: "
            f"{result['tokens_used']} tokens, "
            f"recommendation={parsed_data.get('recommendation')}"
        )

        return {**analysis_data, 'cached': False}

    async def generate_forecast(
        self,
        symbol: str,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Generate two-quarter forecast with scenarios.

        Args:
            symbol: Asset symbol
            force_refresh: If True, bypass cache

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
                logger.info(f"Returning cached forecast for {symbol}")
                return {**cached, 'cached': True}

        logger.info(f"Generating fresh forecast for {symbol}")

        # Fetch prompt
        prompt_template = await self.prompts.get_prompt_by_name("forecast_two_quarters")
        if not prompt_template:
            raise ValueError("Forecast prompt not found")

        # Collect forecast data (position + market context)
        data = await self.data.collect_forecast_data(symbol)

        # Render and generate
        renderer = PromptRenderer()
        rendered_prompt = renderer.render(
            prompt_template.prompt_text,
            prompt_template.template_variables,
            data
        )

        # Request JSON response with lower temperature for consistency
        result = await self.claude.generate_analysis(
            rendered_prompt,
            temperature=0.1
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
        await self.db.commit()

        response = {
            **forecast_data,
            'generated_at': datetime.utcnow(),
            'tokens_used': result['tokens_used'],
            'cached': False
        }

        await self.cache.set(cache_key, response, ttl=86400)  # 24 hours

        logger.info(
            f"Forecast generated for {symbol}: {result['tokens_used']} tokens"
        )

        return response

    async def generate_rebalancing_recommendations(
        self,
        rebalancing_analysis: Any,  # RebalancingAnalysis object
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Generate AI-powered rebalancing recommendations based on allocation analysis.

        Args:
            rebalancing_analysis: RebalancingAnalysis object with current/target allocation
            force_refresh: If True, bypass cache and generate fresh recommendations

        Returns:
            {
                'summary': str,
                'priority': str,  # HIGH/MEDIUM/LOW
                'recommendations': List[RebalancingRecommendation],
                'expected_outcome': ExpectedOutcome,
                'risk_assessment': str,
                'implementation_notes': str,
                'generated_at': datetime,
                'tokens_used': int,
                'cached': bool
            }
        """
        # Early exit if rebalancing not required
        if not rebalancing_analysis.rebalancing_required:
            return {
                'summary': 'Your portfolio is well-balanced. No rebalancing needed.',
                'priority': 'LOW',
                'recommendations': [],
                'expected_outcome': {
                    'stocks_percentage': 0,
                    'crypto_percentage': 0,
                    'metals_percentage': 0,
                    'total_trades': 0,
                    'estimated_costs': 0,
                    'net_allocation_improvement': 'Portfolio is already balanced'
                },
                'risk_assessment': 'None - portfolio is balanced',
                'implementation_notes': 'Review allocation quarterly',
                'generated_at': datetime.utcnow(),
                'tokens_used': 0,
                'cached': False
            }

        cache_key = f"analysis:rebalancing:{rebalancing_analysis.target_model}"

        # Check cache first (6 hours)
        if not force_refresh:
            cached = await self._get_cached_analysis(cache_key)
            if cached:
                # Override cache age check for 6-hour TTL
                age = datetime.utcnow() - cached['generated_at']
                if age < timedelta(hours=6):
                    logger.info("Returning cached rebalancing recommendations")
                    return {**cached, 'cached': True}

        logger.info("Generating fresh rebalancing recommendations")

        # Fetch prompt
        prompt_template = await self.prompts.get_prompt_by_name("portfolio_rebalancing")
        if not prompt_template:
            raise ValueError("Rebalancing prompt not found")

        # Build allocation table
        allocation_table = "| Asset Type | Current % | Target % | Deviation | Status | Delta (EUR) |\n"
        allocation_table += "|------------|-----------|----------|-----------|--------|--------------|\n"
        for alloc in rebalancing_analysis.current_allocation:
            allocation_table += f"| {alloc.asset_type.value} | {alloc.current_percentage:.1f}% | {alloc.target_percentage:.1f}% | {alloc.deviation:+.1f}% | {alloc.status.value} | €{alloc.delta_value:,.2f} |\n"

        # Build positions table
        from rebalancing_service import RebalancingService
        rebalancing_service = RebalancingService(self.db)
        positions_table = "| Symbol | Asset Type | Quantity | Current Price | Value | % of Portfolio |\n"
        positions_table += "|--------|-----------|----------|---------------|-------|----------------|\n"

        for asset_type in rebalancing_analysis.current_allocation:
            positions = await rebalancing_service.get_positions_by_asset_type(asset_type.asset_type)
            for pos in positions:
                value = pos.quantity * pos.current_price if pos.current_price else 0
                pct = (value / rebalancing_analysis.total_portfolio_value * 100) if rebalancing_analysis.total_portfolio_value > 0 else 0
                positions_table += f"| {pos.symbol} | {pos.asset_type.value} | {pos.quantity} | €{pos.current_price:,.2f} | €{value:,.2f} | {pct:.1f}% |\n"

        # Collect market context
        global_data = await self.data.collect_global_data()
        market_indicators = global_data.get('market_indicators', {})

        # Format market indices
        market_indices = f"""
- S&P 500: {market_indicators.get('sp500', {}).get('price', 'N/A')} ({market_indicators.get('sp500', {}).get('change_percent', 'N/A')})
- Bitcoin: ${market_indicators.get('bitcoin', {}).get('price', 'N/A')} ({market_indicators.get('bitcoin', {}).get('change_percent', 'N/A')})
- Gold: ${market_indicators.get('gold', {}).get('price', 'N/A')}/oz ({market_indicators.get('gold', {}).get('change_percent', 'N/A')})
"""

        # Prepare data for prompt rendering
        data = {
            'portfolio_total_value': float(rebalancing_analysis.total_portfolio_value),
            'target_model': rebalancing_analysis.target_model,
            'allocation_table': allocation_table,
            'positions_table': positions_table,
            'market_indices': market_indices
        }

        # Render prompt
        renderer = PromptRenderer()
        rendered_prompt = renderer.render(
            prompt_template.prompt_text,
            prompt_template.template_variables,
            data
        )

        # Generate recommendations
        result = await self.claude.generate_analysis(rendered_prompt)

        # Parse JSON response
        try:
            recommendations_data = self._extract_json_from_response(result['content'])
        except (ValueError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse rebalancing recommendations: {e}")
            raise ValueError("Failed to parse recommendations from AI response")

        # Store in database
        analysis_record = AnalysisResult(
            analysis_type='rebalancing',
            symbol=None,
            prompt_id=prompt_template.id,
            prompt_version=prompt_template.version,
            raw_response=result['content'],
            parsed_data=recommendations_data,
            tokens_used=result['tokens_used'],
            generation_time_ms=result['generation_time_ms'],
            expires_at=datetime.utcnow() + timedelta(hours=6)
        )
        self.db.add(analysis_record)
        await self.db.commit()

        response = {
            **recommendations_data,
            'generated_at': datetime.utcnow(),
            'tokens_used': result['tokens_used'],
            'cached': False
        }

        # Cache for 6 hours
        await self.cache.set(cache_key, response, ttl=21600)  # 6 hours

        logger.info(f"Rebalancing recommendations generated: {result['tokens_used']} tokens")

        return response

    async def _get_cached_analysis(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Check Redis cache for recent analysis.

        Args:
            cache_key: Cache key to check

        Returns:
            Cached analysis data or None
        """
        cached = await self.cache.get(cache_key)
        if cached:
            # Check if still valid (< 24 hours for all analysis types)
            age = datetime.utcnow() - cached['generated_at']
            max_age = timedelta(hours=24)
            if age < max_age:
                return cached
        return None

    def _extract_recommendation(self, analysis_text: str) -> Dict[str, Any]:
        """
        Extract HOLD/BUY_MORE/REDUCE/SELL recommendation from analysis.

        Args:
            analysis_text: Analysis text from Claude

        Returns:
            Dictionary with 'recommendation' key or empty dict
        """
        # First try: Look for recommendation in proper context (e.g., "### Recommendation: **SELL**")
        # This handles markdown formatting with ## or ### headers and **bold** text
        pattern = r'###?\s*Recommendation:\s*\*{0,2}(HOLD|BUY_MORE|REDUCE|SELL)\*{0,2}'
        match = re.search(pattern, analysis_text, re.IGNORECASE)
        if match:
            rec = match.group(1).upper().replace(' ', '_')
            return {'recommendation': rec}

        # Second try: Check in reverse order (most specific first) to avoid false positives
        # This ensures "BUY_MORE" is found before "BUY", and prevents matching "HOLD" in "holdings"
        for rec in ['BUY_MORE', 'REDUCE', 'SELL', 'HOLD']:
            # Use word boundaries to avoid matching substrings
            pattern = r'\b' + rec.replace('_', r'[\s_]') + r'\b'
            if re.search(pattern, analysis_text, re.IGNORECASE):
                return {'recommendation': rec}

        return {}

    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """
        Extract JSON from markdown code block.

        Args:
            response: Response text that may contain ```json...``` block

        Returns:
            Parsed JSON data

        Raises:
            ValueError: If no JSON found in response
        """
        json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        raise ValueError("No JSON found in response")

    def _validate_forecast(self, forecast: Dict[str, Any]):
        """
        Validate forecast structure.

        Args:
            forecast: Forecast data to validate

        Raises:
            ValueError: If forecast structure is invalid
        """
        required_keys = ['q1_forecast', 'q2_forecast', 'overall_outlook']
        if not all(k in forecast for k in required_keys):
            raise ValueError(f"Forecast missing required keys: {required_keys}")

        for quarter in ['q1_forecast', 'q2_forecast']:
            scenarios = forecast[quarter]
            for scenario in ['pessimistic', 'realistic', 'optimistic']:
                if scenario not in scenarios:
                    raise ValueError(f"{quarter} missing {scenario} scenario")

                scenario_data = scenarios[scenario]
                required_fields = ['price', 'confidence', 'assumptions', 'risks']
                missing_fields = [f for f in required_fields if f not in scenario_data]
                if missing_fields:
                    raise ValueError(
                        f"{quarter}.{scenario} missing required fields: {missing_fields}"
                    )
