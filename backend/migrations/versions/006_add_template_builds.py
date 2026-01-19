"""Add template builds support.

Revision ID: 006
Revises: 005
Create Date: 2026-01-19

This migration adds support for build templates:
- is_template: Boolean flag to mark official template builds
- Template builds are read-only (cannot be modified or deleted by users)
- Templates are shown prominently in the frontend

Template builds will be seeded via a separate seed script.
"""
from alembic import op
import sqlalchemy as sa

# Revision identifiers
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    """Add is_template column to builds table."""
    op.add_column(
        'builds',
        sa.Column('is_template', sa.Boolean(), nullable=False, server_default='false')
    )
    
    # Create index for filtering templates
    op.create_index(
        'idx_builds_is_template',
        'builds',
        ['is_template'],
        unique=False
    )


def downgrade():
    """Remove is_template column."""
    op.drop_index('idx_builds_is_template', table_name='builds')
    op.drop_column('builds', 'is_template')
