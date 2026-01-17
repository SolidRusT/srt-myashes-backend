"""Add Steam authentication columns to builds table.

Revision ID: 004
Revises: 003
Create Date: 2026-01-17

This migration adds columns for Steam authentication:
- steam_id: Steam 64-bit ID for the creator
- steam_display_name: Steam persona name at creation time
- player_id: PAM Platform player ID (links to PAM database)

These columns are nullable to maintain backward compatibility with
anonymous builds created before authentication was implemented.
"""
from alembic import op
import sqlalchemy as sa

# Revision identifiers
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    """Add Steam authentication columns."""
    # Add steam_id column to builds table
    op.add_column(
        'builds',
        sa.Column('steam_id', sa.String(64), nullable=True)
    )
    
    # Add steam_display_name column to builds table
    op.add_column(
        'builds',
        sa.Column('steam_display_name', sa.String(100), nullable=True)
    )
    
    # Add player_id column to builds table (PAM Platform reference)
    op.add_column(
        'builds',
        sa.Column('player_id', sa.String(64), nullable=True)
    )
    
    # Create index on steam_id for lookups
    op.create_index(
        'idx_builds_steam_id',
        'builds',
        ['steam_id'],
        unique=False
    )
    
    # Create index on player_id for lookups
    op.create_index(
        'idx_builds_player_id',
        'builds',
        ['player_id'],
        unique=False
    )
    
    # Add steam_id column to build_votes table
    op.add_column(
        'build_votes',
        sa.Column('steam_id', sa.String(64), nullable=True)
    )
    
    # Add player_id column to build_votes table
    op.add_column(
        'build_votes',
        sa.Column('player_id', sa.String(64), nullable=True)
    )
    
    # Create index on build_votes.player_id
    op.create_index(
        'idx_build_votes_player_id',
        'build_votes',
        ['player_id'],
        unique=False
    )
    
    # Update unique constraint on build_votes to include player_id
    # Note: The existing uq_build_vote_user constraint uses user_id
    # We add a new constraint for player_id
    op.create_unique_constraint(
        'uq_build_vote_player',
        'build_votes',
        ['build_id', 'player_id']
    )


def downgrade():
    """Remove Steam authentication columns."""
    # Drop the new unique constraint
    op.drop_constraint('uq_build_vote_player', 'build_votes', type_='unique')
    
    # Drop indexes
    op.drop_index('idx_build_votes_player_id', table_name='build_votes')
    op.drop_index('idx_builds_player_id', table_name='builds')
    op.drop_index('idx_builds_steam_id', table_name='builds')
    
    # Drop columns from build_votes
    op.drop_column('build_votes', 'player_id')
    op.drop_column('build_votes', 'steam_id')
    
    # Drop columns from builds
    op.drop_column('builds', 'player_id')
    op.drop_column('builds', 'steam_display_name')
    op.drop_column('builds', 'steam_id')
