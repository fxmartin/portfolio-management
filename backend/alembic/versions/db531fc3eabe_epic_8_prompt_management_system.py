"""epic_8_prompt_management_system

Revision ID: db531fc3eabe
Revises: 266802e01e3d
Create Date: 2025-10-29 09:02:19.431101

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db531fc3eabe'
down_revision: Union[str, Sequence[str], None] = '266802e01e3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Create prompts, prompt_versions, and analysis_results tables."""
    # Create prompts table
    op.create_table(
        'prompts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('prompt_text', sa.Text(), nullable=False),
        sa.Column('template_variables', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('version', sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create prompt_versions table
    op.create_table(
        'prompt_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prompt_id', sa.Integer(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('prompt_text', sa.Text(), nullable=False),
        sa.Column('changed_by', sa.String(length=100), nullable=True),
        sa.Column('changed_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create analysis_results table
    op.create_table(
        'analysis_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('analysis_type', sa.String(length=50), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=True),
        sa.Column('prompt_id', sa.Integer(), nullable=True),
        sa.Column('prompt_version', sa.Integer(), nullable=True),
        sa.Column('raw_response', sa.Text(), nullable=False),
        sa.Column('parsed_data', sa.JSON(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('generation_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes on analysis_results
    op.create_index('idx_analysis_type_symbol', 'analysis_results', ['analysis_type', 'symbol'])
    op.create_index('idx_analysis_created_at', 'analysis_results', ['created_at'], unique=False, postgresql_ops={'created_at': 'DESC'})


def downgrade() -> None:
    """Downgrade schema - Drop all tables."""
    op.drop_index('idx_analysis_created_at', table_name='analysis_results')
    op.drop_index('idx_analysis_type_symbol', table_name='analysis_results')
    op.drop_table('analysis_results')
    op.drop_table('prompt_versions')
    op.drop_table('prompts')
