"""Phase 3: Add distance_cache table for caching distance matrices

Revision ID: 20251115_1600
Revises: 20251115_1400
Create Date: 2025-11-15 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = '20251115_1600'
down_revision: Union[str, None] = '20251115_1400'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create distance_cache table
    op.create_table(
        'distance_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cache_key', sa.String(length=64), nullable=False),
        sa.Column('distances_meters', JSONB(), nullable=False),
        sa.Column('durations_seconds', JSONB(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index(op.f('ix_distance_cache_id'), 'distance_cache', ['id'], unique=False)
    op.create_index(op.f('ix_distance_cache_cache_key'), 'distance_cache', ['cache_key'], unique=True)
    op.create_index(op.f('ix_distance_cache_expires_at'), 'distance_cache', ['expires_at'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_distance_cache_expires_at'), table_name='distance_cache')
    op.drop_index(op.f('ix_distance_cache_cache_key'), table_name='distance_cache')
    op.drop_index(op.f('ix_distance_cache_id'), table_name='distance_cache')

    # Drop table
    op.drop_table('distance_cache')
