"""Add optimization_metrics table

Revision ID: 20251117_metrics
Revises: 20251116_add_rut
Create Date: 2025-11-17 05:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20251117_metrics'
down_revision: Union[str, None] = '20251116_add_rut'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create optimization_metrics table
    op.create_table(
        'optimization_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('route_id', sa.Integer(), nullable=True),
        sa.Column('optimization_date', sa.Date(), nullable=False),
        sa.Column('optimization_timestamp', sa.DateTime(), nullable=False),
        sa.Column('strategy_used', sa.String(length=50), nullable=False),
        sa.Column('total_cases_requested', sa.Integer(), nullable=False),
        sa.Column('total_cases_assigned', sa.Integer(), nullable=False),
        sa.Column('total_cases_unassigned', sa.Integer(), nullable=False),
        sa.Column('assignment_rate_percentage', sa.Float(), nullable=False),
        sa.Column('optimization_time_seconds', sa.Float(), nullable=False),
        sa.Column('total_distance_km', sa.Float(), nullable=False),
        sa.Column('total_time_minutes', sa.Integer(), nullable=False),
        sa.Column('skill_gaps', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['route_id'], ['routes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index(op.f('ix_optimization_metrics_id'), 'optimization_metrics', ['id'], unique=False)
    op.create_index(op.f('ix_optimization_metrics_optimization_date'), 'optimization_metrics', ['optimization_date'], unique=False)
    op.create_index(op.f('ix_optimization_metrics_route_id'), 'optimization_metrics', ['route_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_optimization_metrics_route_id'), table_name='optimization_metrics')
    op.drop_index(op.f('ix_optimization_metrics_optimization_date'), table_name='optimization_metrics')
    op.drop_index(op.f('ix_optimization_metrics_id'), table_name='optimization_metrics')

    # Drop table
    op.drop_table('optimization_metrics')
