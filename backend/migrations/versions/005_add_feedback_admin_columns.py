"""Add admin review columns to feedback table.

Revision ID: 005
Revises: 004
Create Date: 2026-01-17

This migration adds columns for admin review of AI feedback:
- reviewed_at: Timestamp when feedback was reviewed
- reviewed_by: Steam ID of the admin who reviewed
- flagged_for_cleanup: Whether this feedback indicates bad training data
- cleanup_issue_url: Link to GitHub issue for data layer cleanup

These columns enable the AI Data Quality Dashboard for monitoring
and improving AI response quality.
"""
from alembic import op
import sqlalchemy as sa

# Revision identifiers
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    """Add admin review columns to feedback table."""
    # Add reviewed_at column
    op.add_column(
        'feedback',
        sa.Column('reviewed_at', sa.DateTime, nullable=True)
    )
    
    # Add reviewed_by column (Steam ID of admin)
    op.add_column(
        'feedback',
        sa.Column('reviewed_by', sa.String(64), nullable=True)
    )
    
    # Add flagged_for_cleanup column
    op.add_column(
        'feedback',
        sa.Column('flagged_for_cleanup', sa.Boolean, server_default='false', nullable=False)
    )
    
    # Add cleanup_issue_url column
    op.add_column(
        'feedback',
        sa.Column('cleanup_issue_url', sa.String(256), nullable=True)
    )
    
    # Create index on reviewed_at for filtering
    op.create_index(
        'idx_feedback_reviewed_at',
        'feedback',
        ['reviewed_at'],
        unique=False
    )
    
    # Create index on flagged_for_cleanup for filtering
    op.create_index(
        'idx_feedback_flagged',
        'feedback',
        ['flagged_for_cleanup'],
        unique=False
    )


def downgrade():
    """Remove admin review columns from feedback table."""
    # Drop indexes
    op.drop_index('idx_feedback_flagged', table_name='feedback')
    op.drop_index('idx_feedback_reviewed_at', table_name='feedback')
    
    # Drop columns
    op.drop_column('feedback', 'cleanup_issue_url')
    op.drop_column('feedback', 'flagged_for_cleanup')
    op.drop_column('feedback', 'reviewed_by')
    op.drop_column('feedback', 'reviewed_at')
