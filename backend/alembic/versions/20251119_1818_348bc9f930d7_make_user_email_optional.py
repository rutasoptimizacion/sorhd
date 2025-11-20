"""make_user_email_optional

Revision ID: 348bc9f930d7
Revises: 5cbb35b4f166
Create Date: 2025-11-19 18:18:00.937421

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = '348bc9f930d7'
down_revision: Union[str, None] = '5cbb35b4f166'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make email column nullable
    op.alter_column('users', 'email',
               existing_type=sa.VARCHAR(length=255),
               nullable=True)


def downgrade() -> None:
    # Make email column non-nullable again
    op.alter_column('users', 'email',
               existing_type=sa.VARCHAR(length=255),
               nullable=False)
