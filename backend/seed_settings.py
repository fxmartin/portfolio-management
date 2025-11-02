# ABOUTME: Seed script for populating default application settings
# ABOUTME: Creates 12 default settings across 5 categories with validation rules

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from models import ApplicationSetting, SettingCategory, Base
import asyncio
import os


# Default settings configuration
DEFAULT_SETTINGS = [
    # Display Settings
    {
        "key": "base_currency",
        "value": "EUR",
        "category": SettingCategory.DISPLAY,
        "is_sensitive": False,
        "is_editable": True,
        "description": "Base currency for portfolio display",
        "default_value": "EUR",
        "validation_rules": {"enum": ["EUR", "USD", "GBP", "CHF"]},
    },
    {
        "key": "date_format",
        "value": "YYYY-MM-DD",
        "category": SettingCategory.DISPLAY,
        "is_sensitive": False,
        "is_editable": True,
        "description": "Date format for transaction display",
        "default_value": "YYYY-MM-DD",
        "validation_rules": {"enum": ["YYYY-MM-DD", "DD/MM/YYYY", "MM/DD/YYYY"]},
    },
    {
        "key": "number_format",
        "value": "en-US",
        "category": SettingCategory.DISPLAY,
        "is_sensitive": False,
        "is_editable": True,
        "description": "Number formatting locale",
        "default_value": "en-US",
        "validation_rules": {"enum": ["en-US", "de-DE", "fr-FR", "en-GB"]},
    },
    # API Keys
    {
        "key": "anthropic_api_key",
        "value": None,
        "category": SettingCategory.API_KEYS,
        "is_sensitive": True,
        "is_editable": True,
        "description": "Anthropic Claude API key for AI analysis",
        "default_value": None,
        "validation_rules": {"pattern": "^sk-ant-.*$", "minLength": 20},
    },
    {
        "key": "alpha_vantage_api_key",
        "value": None,
        "category": SettingCategory.API_KEYS,
        "is_sensitive": True,
        "is_editable": True,
        "description": "Alpha Vantage API key for market data fallback",
        "default_value": None,
        "validation_rules": {"minLength": 16, "maxLength": 16},
    },
    # AI Settings (Prompts category)
    {
        "key": "anthropic_model",
        "value": "claude-sonnet-4-5-20250929",
        "category": SettingCategory.PROMPTS,
        "is_sensitive": False,
        "is_editable": True,
        "description": "Claude model to use for analysis",
        "default_value": "claude-sonnet-4-5-20250929",
        "validation_rules": {
            "enum": [
                "claude-sonnet-4-5-20250929",
                "claude-opus-4-20250514",
                "claude-haiku-4-20250702",
            ]
        },
    },
    {
        "key": "anthropic_temperature",
        "value": "0.3",
        "category": SettingCategory.PROMPTS,
        "is_sensitive": False,
        "is_editable": True,
        "description": "Temperature for Claude API (0-1, lower = more focused)",
        "default_value": "0.3",
        "validation_rules": {"type": "number", "minimum": 0, "maximum": 1},
    },
    {
        "key": "anthropic_max_tokens",
        "value": "4096",
        "category": SettingCategory.PROMPTS,
        "is_sensitive": False,
        "is_editable": True,
        "description": "Maximum tokens for Claude responses",
        "default_value": "4096",
        "validation_rules": {"type": "integer", "minimum": 1024, "maximum": 8192},
    },
    # System Settings
    {
        "key": "crypto_price_refresh_seconds",
        "value": "60",
        "category": SettingCategory.SYSTEM,
        "is_sensitive": False,
        "is_editable": True,
        "description": "Crypto price refresh interval (seconds)",
        "default_value": "60",
        "validation_rules": {"type": "integer", "minimum": 30, "maximum": 600},
    },
    {
        "key": "stock_price_refresh_seconds",
        "value": "120",
        "category": SettingCategory.SYSTEM,
        "is_sensitive": False,
        "is_editable": True,
        "description": "Stock price refresh interval (seconds)",
        "default_value": "120",
        "validation_rules": {"type": "integer", "minimum": 60, "maximum": 600},
    },
    {
        "key": "cache_ttl_hours",
        "value": "1",
        "category": SettingCategory.SYSTEM,
        "is_sensitive": False,
        "is_editable": True,
        "description": "Redis cache TTL for analysis results (hours)",
        "default_value": "1",
        "validation_rules": {"type": "integer", "minimum": 1, "maximum": 48},
    },
    # Advanced Settings
    {
        "key": "enable_debug_logging",
        "value": "false",
        "category": SettingCategory.ADVANCED,
        "is_sensitive": False,
        "is_editable": True,
        "description": "Enable debug-level logging",
        "default_value": "false",
        "validation_rules": {"type": "boolean"},
    },
]


async def seed_settings(session: AsyncSession):
    """
    Seed default application settings into the database.

    Args:
        session: Async database session

    Returns:
        int: Number of settings created
    """
    created_count = 0

    for setting_data in DEFAULT_SETTINGS:
        # Check if setting already exists
        from sqlalchemy import select

        result = await session.execute(
            select(ApplicationSetting).filter_by(key=setting_data["key"])
        )
        existing = result.scalar_one_or_none()

        if not existing:
            setting = ApplicationSetting(**setting_data)
            session.add(setting)
            created_count += 1
            print(f"✓ Created setting: {setting_data['key']}")
        else:
            print(f"- Skipped existing setting: {setting_data['key']}")

    await session.commit()
    return created_count


async def main():
    """Main function to run seed script"""
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./portfolio.db")

    # For PostgreSQL URLs, ensure they use asyncpg driver
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")

    print(f"Connecting to database: {database_url}")

    # Create engine and session
    engine = create_async_engine(database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed settings
    async with async_session() as session:
        print("\nSeeding default settings...")
        created_count = await seed_settings(session)
        print(f"\n✅ Seeding complete! Created {created_count} new settings.")
        print(f"Total default settings: {len(DEFAULT_SETTINGS)}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
