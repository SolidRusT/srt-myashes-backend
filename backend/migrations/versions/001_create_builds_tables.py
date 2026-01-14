"""Create builds and build_votes tables

Revision ID: 001
Revises:
Create Date: 2026-01-14

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create builds table
    op.create_table(
        'builds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('build_id', sa.String(12), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('primary_archetype', sa.String(20), nullable=False),
        sa.Column('secondary_archetype', sa.String(20), nullable=False),
        sa.Column('class_name', sa.String(50), nullable=False),
        sa.Column('race', sa.String(20), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False, default=True),
        sa.Column('session_id', sa.String(64), nullable=False),
        sa.Column('user_id', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('rating_sum', sa.Float(), nullable=False, default=0.0),
        sa.Column('vote_count', sa.Integer(), nullable=False, default=0),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_builds_id', 'builds', ['id'], unique=False)
    op.create_index('ix_builds_build_id', 'builds', ['build_id'], unique=True)
    op.create_index('ix_builds_session_id', 'builds', ['session_id'], unique=False)
    op.create_index('ix_builds_user_id', 'builds', ['user_id'], unique=False)
    op.create_index('ix_builds_class_name', 'builds', ['class_name'], unique=False)
    op.create_index('ix_builds_is_public', 'builds', ['is_public'], unique=False)

    # Create build_votes table
    op.create_table(
        'build_votes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('build_id', sa.String(12), nullable=False),
        sa.Column('session_id', sa.String(64), nullable=True),
        sa.Column('user_id', sa.String(64), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['build_id'], ['builds.build_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='ck_vote_rating_range'),
    )
    op.create_index('ix_build_votes_id', 'build_votes', ['id'], unique=False)
    op.create_index('ix_build_votes_build_id', 'build_votes', ['build_id'], unique=False)
    op.create_index('ix_build_votes_session_id', 'build_votes', ['session_id'], unique=False)
    op.create_index('ix_build_votes_user_id', 'build_votes', ['user_id'], unique=False)

    # Unique constraints for one vote per session/user per build
    op.create_unique_constraint('uq_build_vote_session', 'build_votes', ['build_id', 'session_id'])
    op.create_unique_constraint('uq_build_vote_user', 'build_votes', ['build_id', 'user_id'])


def downgrade() -> None:
    op.drop_constraint('uq_build_vote_user', 'build_votes', type_='unique')
    op.drop_constraint('uq_build_vote_session', 'build_votes', type_='unique')
    op.drop_index('ix_build_votes_user_id', table_name='build_votes')
    op.drop_index('ix_build_votes_session_id', table_name='build_votes')
    op.drop_index('ix_build_votes_build_id', table_name='build_votes')
    op.drop_index('ix_build_votes_id', table_name='build_votes')
    op.drop_table('build_votes')

    op.drop_index('ix_builds_is_public', table_name='builds')
    op.drop_index('ix_builds_class_name', table_name='builds')
    op.drop_index('ix_builds_user_id', table_name='builds')
    op.drop_index('ix_builds_session_id', table_name='builds')
    op.drop_index('ix_builds_build_id', table_name='builds')
    op.drop_index('ix_builds_id', table_name='builds')
    op.drop_table('builds')
