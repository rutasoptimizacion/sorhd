"""Phase 2: Add indexes for resource management

Revision ID: 20251115_1400
Revises: fea5abb178de
Create Date: 2025-11-15 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251115_1400'
down_revision: Union[str, None] = 'fea5abb178de'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add indexes for all ID columns to improve query performance
    # These tables are already created from the initial migration
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_care_type_skills_id'), 'care_type_skills', ['id'], unique=False)
    op.create_index(op.f('ix_care_types_id'), 'care_types', ['id'], unique=False)
    op.create_index(op.f('ix_cases_id'), 'cases', ['id'], unique=False)
    op.create_index(op.f('ix_location_logs_id'), 'location_logs', ['id'], unique=False)
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    op.create_index(op.f('ix_patients_id'), 'patients', ['id'], unique=False)
    op.create_index(op.f('ix_personnel_id'), 'personnel', ['id'], unique=False)
    op.create_index(op.f('ix_personnel_skills_id'), 'personnel_skills', ['id'], unique=False)
    op.create_index(op.f('ix_route_personnel_id'), 'route_personnel', ['id'], unique=False)
    op.create_index(op.f('ix_routes_id'), 'routes', ['id'], unique=False)
    op.create_index(op.f('ix_skills_id'), 'skills', ['id'], unique=False)

    # Update users indexes to be unique
    op.drop_constraint('users_email_key', 'users', type_='unique')
    op.drop_constraint('users_username_key', 'users', type_='unique')
    op.drop_index('ix_users_email', table_name='users')
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.drop_index('ix_users_username', table_name='users')
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    op.create_index(op.f('ix_vehicles_id'), 'vehicles', ['id'], unique=False)
    op.create_index(op.f('ix_visits_id'), 'visits', ['id'], unique=False)


def downgrade() -> None:
    # Reverse the index operations
    op.drop_index(op.f('ix_visits_id'), table_name='visits')
    op.drop_index(op.f('ix_vehicles_id'), table_name='vehicles')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.create_index('ix_users_username', 'users', ['username'], unique=False)
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.create_index('ix_users_email', 'users', ['email'], unique=False)
    op.create_unique_constraint('users_username_key', 'users', ['username'])
    op.create_unique_constraint('users_email_key', 'users', ['email'])
    op.drop_index(op.f('ix_skills_id'), table_name='skills')
    op.drop_index(op.f('ix_routes_id'), table_name='routes')
    op.drop_index(op.f('ix_route_personnel_id'), table_name='route_personnel')
    op.drop_index(op.f('ix_personnel_skills_id'), table_name='personnel_skills')
    op.drop_index(op.f('ix_personnel_id'), table_name='personnel')
    op.drop_index(op.f('ix_patients_id'), table_name='patients')
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_index(op.f('ix_location_logs_id'), table_name='location_logs')
    op.drop_index(op.f('ix_cases_id'), table_name='cases')
    op.drop_index(op.f('ix_care_types_id'), table_name='care_types')
    op.drop_index(op.f('ix_care_type_skills_id'), table_name='care_type_skills')
    op.drop_index(op.f('ix_audit_logs_id'), table_name='audit_logs')
