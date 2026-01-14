"""Create search_analytics table

Revision ID: 003
Revises: 002
Create Date: 2026-01-14

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create search_analytics table
    op.create_table(
        'search_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('search_mode', sa.String(10), nullable=False),
        sa.Column('result_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('session_id', sa.String(64), nullable=True),
        sa.Column('user_id', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_search_analytics_id', 'search_analytics', ['id'], unique=False)
    op.create_index('ix_search_analytics_session_id', 'search_analytics', ['session_id'], unique=False)
    op.create_index('ix_search_analytics_user_id', 'search_analytics', ['user_id'], unique=False)
    op.create_index('ix_search_analytics_created_at', 'search_analytics', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_search_analytics_created_at', table_name='search_analytics')
    op.drop_index('ix_search_analytics_user_id', table_name='search_analytics')
    op.drop_index('ix_search_analytics_session_id', table_name='search_analytics')
    op.drop_index('ix_search_analytics_id', table_name='search_analytics')
    op.drop_table('search_analytics')
