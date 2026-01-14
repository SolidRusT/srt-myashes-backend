"""Create feedback table

Revision ID: 002
Revises: 001
Create Date: 2026-01-14

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create feedback table
    op.create_table(
        'feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('feedback_id', sa.String(12), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('response_snippet', sa.Text(), nullable=False),
        sa.Column('search_mode', sa.String(10), nullable=False),
        sa.Column('rating', sa.String(4), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('session_id', sa.String(64), nullable=True),
        sa.Column('user_id', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_feedback_id', 'feedback', ['id'], unique=False)
    op.create_index('ix_feedback_feedback_id', 'feedback', ['feedback_id'], unique=True)
    op.create_index('ix_feedback_session_id', 'feedback', ['session_id'], unique=False)
    op.create_index('ix_feedback_user_id', 'feedback', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_feedback_user_id', table_name='feedback')
    op.drop_index('ix_feedback_session_id', table_name='feedback')
    op.drop_index('ix_feedback_feedback_id', table_name='feedback')
    op.drop_index('ix_feedback_id', table_name='feedback')
    op.drop_table('feedback')
