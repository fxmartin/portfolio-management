"""epic_9_settings_management_system

Revision ID: 2401361c88a1
Revises: 9f9d631d0cb8
Create Date: 2025-11-02 19:00:41.640189

Epic 9: Settings Management - F9.1-001
Creates application_settings and setting_history tables for storing
encrypted settings with validation rules and audit trail.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '2401361c88a1'
down_revision: Union[str, Sequence[str], None] = '9f9d631d0cb8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create application_settings and setting_history tables for F9.1-001.

    Features:
    - Stores application configuration with encryption support
    - Categorized settings (display, api_keys, prompts, system, advanced)
    - JSON schema validation rules
    - Audit trail for all setting changes
    - Unique key constraint for settings
    - Indexed by category for fast queries
    """
    # Create setting_category enum
    setting_category_enum = sa.Enum(
        'display', 'api_keys', 'prompts', 'system', 'advanced',
        name='settingcategory',
        create_type=True
    )

    # Create application_settings table
    op.create_table(
        'application_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(100), nullable=False, unique=True),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('category', setting_category_enum, nullable=False),
        sa.Column('is_sensitive', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_editable', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('default_value', sa.Text(), nullable=True),
        sa.Column('validation_rules', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('last_modified_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key', name='uq_application_settings_key')
    )

    # Create indexes for application_settings
    op.create_index('idx_settings_key', 'application_settings', ['key'])
    op.create_index('idx_settings_category', 'application_settings', ['category'])

    # Create setting_history table
    op.create_table(
        'setting_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('setting_id', sa.Integer(), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('changed_by', sa.String(100), nullable=False, server_default='system'),
        sa.Column('changed_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['setting_id'], ['application_settings.id'], name='fk_setting_history_setting_id')
    )

    # Create indexes for setting_history
    op.create_index('idx_setting_history_setting', 'setting_history', ['setting_id', 'changed_at'])


def downgrade() -> None:
    """
    Drop application_settings and setting_history tables.
    """
    # Drop indexes first
    op.drop_index('idx_setting_history_setting', table_name='setting_history')
    op.drop_index('idx_settings_category', table_name='application_settings')
    op.drop_index('idx_settings_key', table_name='application_settings')

    # Drop tables
    op.drop_table('setting_history')
    op.drop_table('application_settings')

    # Drop enum type
    sa.Enum(name='settingcategory').drop(op.get_bind(), checkfirst=True)
