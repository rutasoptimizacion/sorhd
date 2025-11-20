"""add_first_login_to_users

Revision ID: 5cbb35b4f166
Revises: 20251117_metrics
Create Date: 2025-11-19 02:41:15.687259

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = '5cbb35b4f166'
down_revision: Union[str, None] = '20251117_metrics'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add first_login column to users table
    # 1 = needs activation (first time), 0 = already activated
    op.add_column('users', sa.Column('first_login', sa.Integer(), nullable=False, server_default='1'))


def downgrade() -> None:
    # Remove first_login column
    op.drop_column('users', 'first_login')
