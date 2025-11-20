"""Make personnel start_location optional

Revision ID: 20251116_0900
Revises: 006
Create Date: 2025-11-16 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geography


# revision identifiers, used by Alembic.
revision: str = '20251116_0900'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make start_location nullable
    op.alter_column('personnel', 'start_location',
                    existing_type=Geography(geometry_type='POINT', srid=4326, spatial_index=False),
                    nullable=True)


def downgrade() -> None:
    # Make start_location NOT NULL again
    # Note: This will fail if there are NULL values in the column
    op.alter_column('personnel', 'start_location',
                    existing_type=Geography(geometry_type='POINT', srid=4326, spatial_index=False),
                    nullable=False)
