# ABOUTME: Seed script for populating default AI analysis prompts
# ABOUTME: Creates 3 default prompts (global, position, forecast) for AI market analysis

"""
Seed script for Epic 8: AI-Powered Market Analysis

This script populates the database with default prompt templates for:
1. Global market analysis
2. Position-specific analysis
3. Two-quarter forecasts with scenarios

Run with: uv run python seed_prompts.py
Or import and call: seed_default_prompts(session)
"""

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from models import Prompt
from database import get_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


DEFAULT_PROMPTS = [
    {
        "name": "global_market_analysis",
        "category": "global",
        "prompt_text": """You are a professional financial analyst providing market insights for a portfolio management application.

Current Portfolio Context:
- Total Value: €{portfolio_value}
- Asset Allocation: {asset_allocation}
- Open Positions: {position_count}
- Top Holdings: {top_holdings}

{market_context}

{global_crypto_context}

Provide a succinct market analysis (250-350 words) covering:
1. **Market Environment**: Reference key indicators (VIX, yields, dollar strength) and their implications for this portfolio
2. **Asset Class Outlook**: How are equities (especially EU markets for AMEM/MWOQ), commodities, and crypto positioned?
3. **Portfolio-Specific Risks**: Given current market conditions and allocation, what are the key risks?
4. **Actionable Insights**: Any immediate portfolio adjustments suggested by market conditions?

Be direct, data-driven, and actionable. Reference specific market indicators when relevant.""",
        "template_variables": {
            "portfolio_value": "decimal",
            "asset_allocation": "object",
            "position_count": "integer",
            "top_holdings": "array",
            "market_context": "string",
            "global_crypto_context": "string"
        }
    },
    {
        "name": "position_analysis",
        "category": "position",
        "prompt_text": """Analyze the following investment position for a personal portfolio:

Asset: {symbol} ({name})
Sector: {sector} | Type: {asset_type}

Position Overview:
- Holdings: {quantity} units
- Current Market Value: €{current_value}
- Total Cost Basis: €{cost_basis}
- Average Cost per Unit: €{avg_cost_per_unit}
- Current Price per Unit: €{current_price}

Performance:
- Unrealized P&L: €{unrealized_pnl} ({pnl_percentage}%)
- Position Weight: {position_percentage}% of portfolio
- 24h Price Change: {day_change}%

Market Context:
- 24h Trading Volume: {volume}
{fear_greed_context}

{crypto_context}

Provide analysis (150-200 words) covering:
1. Current market position and recent performance
2. Key factors driving price movement (consider market sentiment if crypto asset)
3. Risk assessment for this holding
4. Recommended action: HOLD, BUY_MORE, REDUCE, or SELL (with brief rationale)

IMPORTANT: Use the provided P&L percentage ({pnl_percentage}%) as the definitive performance metric. Do not recalculate P&L from price values.

Be concise and actionable.""",
        "template_variables": {
            "symbol": "string",
            "name": "string",
            "quantity": "decimal",
            "current_value": "decimal",
            "current_price": "decimal",
            "cost_basis": "decimal",
            "avg_cost_per_unit": "decimal",
            "unrealized_pnl": "decimal",
            "pnl_percentage": "decimal",
            "position_percentage": "decimal",
            "day_change": "decimal",
            "sector": "string",
            "asset_type": "string",
            "volume": "integer",
            "fear_greed_context": "string",
            "crypto_context": "string"
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
{{
  "q1_forecast": {{
    "pessimistic": {{"price": X, "confidence": Y, "assumptions": "...", "risks": "..."}},
    "realistic": {{"price": X, "confidence": Y, "assumptions": "...", "risks": "..."}},
    "optimistic": {{"price": X, "confidence": Y, "assumptions": "...", "risks": "..."}}
  }},
  "q2_forecast": {{ ... same structure ... }},
  "overall_outlook": "Brief 2-3 sentence summary"
}}""",
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


async def seed_default_prompts_async(db: AsyncSession) -> dict:
    """
    Seed database with default prompts (async version for AsyncSession)

    Returns:
        dict: Summary with counts of created, skipped, and updated prompts
    """
    created = 0
    skipped = 0
    updated = 0

    for prompt_data in DEFAULT_PROMPTS:
        # Check if prompt already exists
        result = await db.execute(select(Prompt).filter_by(name=prompt_data["name"]))
        existing = result.scalar_one_or_none()

        if existing:
            # Update if text has changed
            if existing.prompt_text != prompt_data["prompt_text"]:
                logger.info(f"Updating existing prompt: {prompt_data['name']}")
                existing.prompt_text = prompt_data["prompt_text"]
                existing.template_variables = prompt_data["template_variables"]
                existing.version += 1
                updated += 1
            else:
                logger.info(f"Prompt already exists (unchanged): {prompt_data['name']}")
                skipped += 1
        else:
            # Create new prompt
            logger.info(f"Creating new prompt: {prompt_data['name']}")
            new_prompt = Prompt(
                name=prompt_data["name"],
                category=prompt_data["category"],
                prompt_text=prompt_data["prompt_text"],
                template_variables=prompt_data["template_variables"],
                is_active=1,
                version=1
            )
            db.add(new_prompt)
            created += 1

    await db.commit()

    summary = {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "total": len(DEFAULT_PROMPTS)
    }

    logger.info(f"Seed complete: {summary}")
    return summary


def seed_default_prompts(db: Session) -> dict:
    """
    Seed database with default prompts (sync version for regular Session)

    Returns:
        dict: Summary with counts of created, skipped, and updated prompts
    """
    created = 0
    skipped = 0
    updated = 0

    for prompt_data in DEFAULT_PROMPTS:
        # Check if prompt already exists
        existing = db.query(Prompt).filter(Prompt.name == prompt_data["name"]).first()

        if existing:
            # Update if text has changed
            if existing.prompt_text != prompt_data["prompt_text"]:
                logger.info(f"Updating existing prompt: {prompt_data['name']}")
                existing.prompt_text = prompt_data["prompt_text"]
                existing.template_variables = prompt_data["template_variables"]
                existing.version += 1
                updated += 1
            else:
                logger.info(f"Prompt already exists (unchanged): {prompt_data['name']}")
                skipped += 1
        else:
            # Create new prompt
            logger.info(f"Creating new prompt: {prompt_data['name']}")
            new_prompt = Prompt(
                name=prompt_data["name"],
                category=prompt_data["category"],
                prompt_text=prompt_data["prompt_text"],
                template_variables=prompt_data["template_variables"],
                is_active=1,
                version=1
            )
            db.add(new_prompt)
            created += 1

    db.commit()

    summary = {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "total": len(DEFAULT_PROMPTS)
    }

    logger.info(f"Seed complete: {summary}")
    return summary


if __name__ == "__main__":
    """Run seed script directly"""
    from database import SessionLocal

    db = SessionLocal()
    try:
        result = seed_default_prompts(db)
        print(f"\n✅ Seed completed successfully!")
        print(f"   Created: {result['created']}")
        print(f"   Updated: {result['updated']}")
        print(f"   Skipped: {result['skipped']}")
        print(f"   Total:   {result['total']}\n")
    except Exception as e:
        logger.error(f"Seed failed: {e}")
        raise
    finally:
        db.close()
