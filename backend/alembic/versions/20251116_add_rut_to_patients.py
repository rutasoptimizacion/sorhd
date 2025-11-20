"""Add RUT field to patients table

Revision ID: 20251116_add_rut
Revises: 20251116_0900
Create Date: 2025-11-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251116_add_rut'
down_revision: Union[str, None] = '20251116_0900'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add RUT column to patients table

    RUT (Rol Único Tributario) is the Chilean national identification number.
    - Optional (nullable=True)
    - Unique constraint
    - Indexed for fast lookups
    - Max length 12 chars (stores cleaned format without dots/hyphens)
    """
    # Add rut column
    op.add_column('patients',
        sa.Column('rut', sa.String(length=12), nullable=True)
    )

    # Create unique constraint
    op.create_unique_constraint('uq_patients_rut', 'patients', ['rut'])

    # Create index for faster lookups
    op.create_index('ix_patients_rut', 'patients', ['rut'], unique=False)


def downgrade() -> None:
    """Remove RUT column from patients table"""
    # Drop index
    op.drop_index('ix_patients_rut', table_name='patients')

    # Drop unique constraint
    op.drop_constraint('uq_patients_rut', 'patients', type_='unique')

    # Drop column
    op.drop_column('patients', 'rut')
