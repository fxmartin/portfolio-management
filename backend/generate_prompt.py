import asyncio
from database import get_async_db
from sqlalchemy import select
from models import InvestmentStrategy, Position, Prompt
from prompt_renderer import PromptDataCollector, PromptRenderer
from portfolio_service import PortfolioService
from yahoo_finance_service import YahooFinanceService

DEFAULT_USER_ID = 1

async def generate_prompt():
    async for db in get_async_db():
        try:
            # Get strategy
            result = await db.execute(
                select(InvestmentStrategy).where(InvestmentStrategy.user_id == DEFAULT_USER_ID)
            )
            strategy = result.scalar_one_or_none()

            if not strategy:
                print('ERROR: No strategy found')
                return

            # Get positions
            result = await db.execute(select(Position))
            positions = list(result.scalars().all())

            # Get prompt template
            result = await db.execute(
                select(Prompt).where(Prompt.name == 'strategy_driven_recommendations')
            )
            prompt_template = result.scalar_one_or_none()

            if not prompt_template:
                print('ERROR: No prompt template found')
                return

            # Collect data
            portfolio_service = PortfolioService(db)
            yahoo_service = YahooFinanceService()
            data_collector = PromptDataCollector(
                db, portfolio_service, yahoo_service,
                None, None, None
            )

            data = await data_collector.collect_strategy_analysis_data(strategy, positions)

            # Render prompt
            renderer = PromptRenderer()
            rendered = renderer.render(
                prompt_template.prompt_text,
                prompt_template.template_variables,
                data
            )

            print(rendered)
            break
        finally:
            await db.close()

if __name__ == '__main__':
    asyncio.run(generate_prompt())
