"""epic_8_f8_8_investment_strategy

Revision ID: 9f9d631d0cb8
Revises: db531fc3eabe
Create Date: 2025-11-01 21:48:50.020998

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f9d631d0cb8'
down_revision: Union[str, Sequence[str], None] = 'db531fc3eabe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create investment_strategy table for F8.8-001.

    Features:
    - Stores user investment strategies with goals and constraints
    - UNIQUE constraint on user_id (one strategy per user)
    - Auto-incrementing version on UPDATE via trigger
    - Optional fields for target return, risk tolerance, time horizon, etc.
    """
    # Create investment_strategy table
    op.create_table(
        'investment_strategy',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('strategy_text', sa.String(), nullable=False),  # TEXT in PostgreSQL
        sa.Column('target_annual_return', sa.Numeric(5, 2), nullable=True),
        sa.Column('risk_tolerance', sa.String(10), nullable=True),  # LOW, MEDIUM, HIGH, CUSTOM
        sa.Column('time_horizon_years', sa.Integer(), nullable=True),
        sa.Column('max_positions', sa.Integer(), nullable=True),
        sa.Column('profit_taking_threshold', sa.Numeric(5, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_investment_strategy_user_id')
    )

    # Create index on user_id for fast lookups
    op.create_index('idx_investment_strategy_user_id', 'investment_strategy', ['user_id'])

    # Create trigger function to auto-increment version on UPDATE
    # This ensures version tracking without application-level logic
    op.execute("""
        CREATE OR REPLACE FUNCTION update_strategy_version()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.version = OLD.version + 1;
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create trigger on UPDATE to call version function
    op.execute("""
        CREATE TRIGGER trigger_update_strategy_version
        BEFORE UPDATE ON investment_strategy
        FOR EACH ROW
        EXECUTE FUNCTION update_strategy_version();
    """)


def downgrade() -> None:
    """Drop investment_strategy table and trigger."""
    # Drop trigger first
    op.execute('DROP TRIGGER IF EXISTS trigger_update_strategy_version ON investment_strategy;')

    # Drop trigger function
    op.execute('DROP FUNCTION IF EXISTS update_strategy_version();')

    # Drop index
    op.drop_index('idx_investment_strategy_user_id', table_name='investment_strategy')

    # Drop table
    op.drop_table('investment_strategy')
