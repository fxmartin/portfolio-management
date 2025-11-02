# ABOUTME: Seed script for populating default AI analysis prompts
# ABOUTME: Creates 5 default prompts (rebalancing, global, position, forecast, strategy-driven) for AI market analysis

"""
Seed script for Epic 8: AI-Powered Market Analysis

This script populates the database with default prompt templates for:
1. Portfolio rebalancing recommendations
2. Global market analysis
3. Position-specific analysis
4. Two-quarter forecasts with scenarios
5. Strategy-driven portfolio recommendations (F8.8-002)

Run with: uv run python seed_prompts.py
Or import and call: seed_default_prompts(session)
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from models import Prompt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


DEFAULT_PROMPTS = [
    {
        "name": "portfolio_rebalancing",
        "category": "rebalancing",
        "prompt_text": """You are a portfolio advisor providing specific rebalancing recommendations.

## Current Portfolio State

**Total Value**: €{portfolio_total_value}
**Target Allocation Model**: {target_model}

## Current Allocation vs Target

{allocation_table}

## Current Positions

{positions_table}

## Market Context

{market_indices}

## Instructions

Generate specific rebalancing recommendations to achieve the target allocation:

1. **Identify specific positions to reduce** (OVERWEIGHT assets)
   - Which symbols to sell and how much
   - Consider current market conditions and tax implications
   - Prioritize positions with gains to minimize losses

2. **Identify specific positions to increase or new positions to open** (UNDERWEIGHT assets)
   - Which symbols to buy and how much
   - Consider diversification within the asset type
   - Suggest specific entry points if possible

3. **Prioritize recommendations** by largest deviations first

4. **Provide rationale** for each recommendation explaining:
   - Why this specific position
   - How it addresses the allocation gap
   - Market timing considerations
   - Risk/reward assessment

5. **Consider practical constraints**:
   - Minimum trade sizes (don't suggest trades <€50)
   - Transaction costs (assume 0.5% per trade)
   - Avoid creating too many small positions

## Response Format

Return recommendations in this JSON structure:

```json
{{
  "summary": "Overall rebalancing strategy summary in 2-3 sentences",
  "priority": "HIGH|MEDIUM|LOW based on deviation severity",
  "recommendations": [
    {{
      "action": "SELL",
      "symbol": "BTC",
      "asset_type": "crypto",
      "quantity": 0.05,
      "current_price": 81234.56,
      "estimated_value": 4061.73,
      "rationale": "Reduce crypto exposure from 35% to 25%. BTC is overweight and currently showing strength (+2.3% today) - good opportunity to lock in gains.",
      "priority": 1,
      "timing": "Consider selling into current strength (+2.3% today)",
      "transaction_data": {{
        "transaction_type": "SELL",
        "symbol": "BTC",
        "quantity": 0.05,
        "price": 81234.56,
        "total_value": 4061.73,
        "currency": "EUR",
        "notes": "Rebalancing: Reduce crypto from 35% to 25% target"
      }}
    }}
  ],
  "expected_outcome": {{
    "stocks_percentage": 60.0,
    "crypto_percentage": 25.0,
    "metals_percentage": 15.0,
    "total_trades": 5,
    "estimated_costs": 125.50,
    "net_allocation_improvement": "+15% closer to target"
  }},
  "risk_assessment": "Low - Recommendations diversified across asset types...",
  "implementation_notes": "Execute in 2-3 tranches over 1 week to minimize market impact"
}}
```

Be specific with quantities and EUR amounts. Ensure all recommendations together achieve the target allocation.""",
        "template_variables": {
            "portfolio_total_value": "decimal",
            "target_model": "string",
            "allocation_table": "string",
            "positions_table": "string",
            "market_indices": "string"
        }
    },
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
            "top_holdings": "string",  # Pre-formatted string from _format_holdings_list()
            "market_context": "string",
            "global_crypto_context": "string"
        }
    },
    {
        "name": "position_analysis",
        "category": "position",
        "prompt_text": """Analyze the following investment position within the context of the full portfolio:

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

## Portfolio Context (Strategic View)

{portfolio_context}

**Concentration Analysis**: This position represents {position_percentage}% of your total portfolio.

Provide analysis (200-300 words) covering:
1. **Position Performance**: Current market position and recent performance
2. **Market Drivers**: Key factors driving price movement (consider market sentiment if crypto asset)
3. **Portfolio Fit**: How does this position fit your overall allocation? Is this sector/asset type over/underweight?
4. **Concentration Risk**: Given your portfolio composition, does this position create concentration risk?
5. **Strategic Recommendation**: HOLD, BUY_MORE, REDUCE, or SELL

**Recommendation Considerations**:
- If your portfolio is already heavily concentrated in this sector (>50%), suggest REDUCE even for performing assets
- If diversification is poor (top 3 positions > 60%), recommend rebalancing
- Consider both tactical (asset performance) AND strategic (portfolio balance) factors
- Reference specific portfolio metrics when relevant (e.g., "Technology sector is 75% of stock holdings")

IMPORTANT:
- Use the provided P&L percentage ({pnl_percentage}%) as the definitive performance metric
- Your recommendation MUST consider both individual asset merit AND portfolio-level diversification
- Be direct about concentration risks - better diversification beats individual asset upside

Be concise, data-driven, and strategic.""",
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
            "crypto_context": "string",
            "portfolio_context": "string"
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
    },
    {
        "name": "strategy_driven_recommendations",
        "category": "strategy",
        "prompt_text": """You are a portfolio advisor analyzing how well a portfolio aligns with the user's investment strategy and providing actionable recommendations.

## User's Investment Strategy

**Strategy Statement**: {strategy_text}

**Target Annual Return**: {target_annual_return}%
**Risk Tolerance**: {risk_tolerance}
**Time Horizon**: {time_horizon_years} years
**Maximum Positions**: {max_positions}
**Profit-Taking Threshold**: {profit_taking_threshold}%

## Current Portfolio

**Total Value**: €{portfolio_total_value}
**Number of Positions**: {position_count}

### Asset Allocation
{asset_allocation}

### Current Positions
{positions_table}

### Portfolio Concentration
- Top 3 positions: {top_3_weight}%
- Largest single position: {single_asset_max}%
- Largest sector: {single_sector_max}%

## Analysis Tasks

1. **Profit-Taking Assessment**:
   - Identify positions that have exceeded the {profit_taking_threshold}% profit threshold
   - Consider holding period and tax implications
   - For each opportunity, provide specific transaction_data with exact SELL quantities

2. **Position Alignment Review**:
   - Evaluate each position against the stated strategy
   - Flag positions that don't fit the strategy (MISALIGNED)
   - Identify overweight positions that need reduction

3. **New Position Suggestions**:
   - Recommend new positions to better align with the strategy
   - Consider gaps in diversification
   - Suggest specific symbols with rationale

4. **Action Plan**:
   - Create prioritized list of actions (1=highest priority)
   - Include specific transaction_data for BUY/SELL actions
   - Balance profit-taking with strategic rebalancing

5. **Target Return Assessment**:
   - Evaluate if the target annual return ({target_annual_return}%) is achievable
   - Identify required changes to reach the target
   - Assess risk level needed

## Response Format

Return a valid JSON object with the following structure:

**Required Fields**:
- `summary` (string): 2-3 sentence executive summary of portfolio alignment and key recommendations
- `alignment_score` (number): Score from 0-10 indicating how well portfolio aligns with strategy
- `key_insights` (array of strings): 3-5 critical observations about the portfolio
- `profit_taking_opportunities` (array of objects): Positions exceeding profit threshold
  - Each with: symbol, current_value, entry_cost, unrealized_gain, gain_percentage, recommendation, rationale, transaction_data
- `position_assessments` (array of objects): Evaluation of each position against strategy
  - Each with: symbol, current_allocation, strategic_fit (ALIGNED/OVERWEIGHT/UNDERWEIGHT/MISALIGNED), action_needed (HOLD/REDUCE/INCREASE/SELL), rationale
- `new_position_suggestions` (array of objects): Recommended new positions to improve alignment
  - Each with: symbol, asset_type, rationale, suggested_allocation, entry_strategy
- `action_plan` (object): Prioritized actions organized by timeframe
  - `immediate_actions` (array): High priority actions to execute now (each with priority number, action, details, expected_impact, transaction_data if applicable)
  - `redeployment` (array): How to reinvest proceeds from sales
  - `gradual_adjustments` (array): Longer-term portfolio changes
- `target_annual_return_assessment` (object): Evaluation of return goal achievability
  - Fields: target_return, current_projected_return, achievability (ACHIEVABLE/CHALLENGING/UNREALISTIC), required_changes, risk_level
- `risk_assessment` (string): Overall assessment of portfolio risk vs strategy
- `next_review_date` (string): Recommended date for next review (YYYY-MM-DD format)

## Important Guidelines

- Be specific: Provide exact quantities, prices, and EUR values in transaction_data
- Be realistic: Consider current market conditions and practical constraints
- Be strategic: Balance profit-taking, diversification, and long-term goals
- Be honest: If the target return is unrealistic, say so clearly
- Prioritize actions: Most important actions first (priority 1, 2, 3...)
- Focus on alignment: Every recommendation should reference the stated strategy

Generate comprehensive recommendations that help the user achieve their investment goals while managing risk appropriately.""",
        "template_variables": {
            "strategy_text": "string",
            "target_annual_return": "decimal",
            "risk_tolerance": "string",
            "time_horizon_years": "integer",
            "max_positions": "integer",
            "profit_taking_threshold": "decimal",
            "portfolio_total_value": "decimal",
            "position_count": "integer",
            "asset_allocation": "string",
            "positions_table": "string",
            "top_3_weight": "decimal",
            "single_asset_max": "decimal",
            "single_sector_max": "decimal"
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
        print("\n✅ Seed completed successfully!")
        print(f"   Created: {result['created']}")
        print(f"   Updated: {result['updated']}")
        print(f"   Skipped: {result['skipped']}")
        print(f"   Total:   {result['total']}\n")
    except Exception as e:
        logger.error(f"Seed failed: {e}")
        raise
    finally:
        db.close()
