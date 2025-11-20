"""notification system updates

Revision ID: 006
Revises: 20251115_1600
Create Date: 2025-11-15

Updates:
- Add phone_number and device_token to users table
- Update notifications table structure
- Add new notification types
- Add delivery tracking fields
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '20251115_1600'
branch_labels = None
depends_on = None


def upgrade():
    # Add notification fields to users table
    op.add_column('users', sa.Column('phone_number', sa.String(20), nullable=True))
    op.add_column('users', sa.Column('device_token', sa.String(255), nullable=True))

    # Check if notifications table exists, if not create it
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = inspector.get_table_names()

    if 'notifications' not in tables:
        # Create notifications table
        op.create_table(
            'notifications',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, index=True),
            sa.Column('type', sa.String(50), nullable=False, index=True),
            sa.Column('title', sa.String(255), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('data', postgresql.JSONB(), nullable=True),
            sa.Column('status', sa.String(50), nullable=False, index=True),
            sa.Column('delivery_channel', sa.String(50), nullable=True),
            sa.Column('provider_message_id', sa.String(255), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('sent_at', sa.DateTime(), nullable=True),
            sa.Column('read_at', sa.DateTime(), nullable=True, index=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
        )

        # Create indexes
        op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
        op.create_index('ix_notifications_type', 'notifications', ['type'])
        op.create_index('ix_notifications_status', 'notifications', ['status'])
        op.create_index('ix_notifications_read_at', 'notifications', ['read_at'])
    else:
        # Update existing notifications table

        # Rename notification_type to type if it exists
        columns = [col['name'] for col in inspector.get_columns('notifications')]

        if 'notification_type' in columns:
            op.alter_column('notifications', 'notification_type', new_column_name='type')

        # Rename channel to delivery_channel if it exists
        if 'channel' in columns:
            op.alter_column('notifications', 'channel', new_column_name='delivery_channel')

        # Add new columns if they don't exist
        if 'data' not in columns:
            op.add_column('notifications', sa.Column('data', postgresql.JSONB(), nullable=True))

        if 'provider_message_id' not in columns:
            op.add_column('notifications', sa.Column('provider_message_id', sa.String(255), nullable=True))

        if 'sent_at' not in columns:
            op.add_column('notifications', sa.Column('sent_at', sa.DateTime(), nullable=True))

        if 'read_at' not in columns:
            op.add_column('notifications', sa.Column('read_at', sa.DateTime(), nullable=True))
            # Create index
            op.create_index('ix_notifications_read_at', 'notifications', ['read_at'])

        # Remove is_read column if it exists (replaced by read_at)
        if 'is_read' in columns:
            # First, migrate data: set read_at to now for is_read=true
            connection.execute(sa.text(
                "UPDATE notifications SET read_at = updated_at WHERE is_read = true"
            ))
            op.drop_column('notifications', 'is_read')


def downgrade():
    # Remove notification fields from users table
    op.drop_column('users', 'device_token')
    op.drop_column('users', 'phone_number')

    # Revert notifications table changes
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if 'notifications' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('notifications')]

        # Add back is_read if it was removed
        if 'is_read' not in columns:
            op.add_column('notifications', sa.Column('is_read', sa.Boolean(), default=False, nullable=False))
            # Migrate data back
            connection.execute(sa.text(
                "UPDATE notifications SET is_read = true WHERE read_at IS NOT NULL"
            ))

        # Remove new columns
        if 'read_at' in columns:
            op.drop_index('ix_notifications_read_at', 'notifications')
            op.drop_column('notifications', 'read_at')

        if 'sent_at' in columns:
            op.drop_column('notifications', 'sent_at')

        if 'provider_message_id' in columns:
            op.drop_column('notifications', 'provider_message_id')

        # Rename columns back
        if 'type' in columns:
            op.alter_column('notifications', 'type', new_column_name='notification_type')

        if 'delivery_channel' in columns:
            op.alter_column('notifications', 'delivery_channel', new_column_name='channel')

        # Convert JSONB back to Text if needed
        if 'data' in columns:
            op.alter_column('notifications', 'data', type_=sa.Text(), postgresql_using='data::text')
