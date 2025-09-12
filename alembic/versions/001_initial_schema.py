"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from geoalchemy2 import Geometry

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable PostGIS extension
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')
    
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.Text(), nullable=False),
        sa.Column('email_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('name', sa.Text(), nullable=True),
        sa.Column('phone', sa.Text(), nullable=True),
        sa.Column('school', sa.Text(), nullable=True),
        sa.Column('year', sa.Text(), nullable=True),
        sa.Column('verified_status', sa.Text(), nullable=False, default='unverified'),
        sa.Column('eco_points', sa.Integer(), nullable=False, default=0),
        sa.Column('owner_max_bikes', sa.Integer(), nullable=False, default=1),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("verified_status IN ('unverified','pending','verified','rejected')", name='users_verified_status_check')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Create devices table
    op.create_table('devices',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('expo_push_token', sa.Text(), nullable=True),
        sa.Column('platform', sa.Text(), nullable=True),
        sa.Column('last_seen', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create docks table
    op.create_table('docks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('geom', Geometry('POINT', srid=4326), nullable=False),
        sa.Column('capacity', sa.Integer(), nullable=False, default=10),
        sa.Column('available_count', sa.Integer(), nullable=False, default=0),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create zones table
    op.create_table('zones',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('kind', sa.Text(), nullable=False),
        sa.Column('polygon', Geometry('POLYGON', srid=4326), nullable=False),
        sa.Column('label', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, default=1),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("kind IN ('green','red')", name='zones_kind_check')
    )
    
    # Create bikes table
    op.create_table('bikes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('type', sa.Text(), nullable=False, default='standard'),
        sa.Column('condition', sa.Text(), nullable=False, default='B'),
        sa.Column('hourly_rate', sa.Integer(), nullable=False, default=50),
        sa.Column('dock_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.Text(), nullable=False, default='available'),
        sa.Column('qr_token_hash', sa.Text(), nullable=True),
        sa.Column('gps_tracker_id', sa.Text(), nullable=True),
        sa.Column('photos', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['dock_id'], ['docks.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("type IN ('standard','premium','old')", name='bikes_type_check'),
        sa.CheckConstraint("condition IN ('A','B','C')", name='bikes_condition_check'),
        sa.CheckConstraint("status IN ('available','rented','maintenance','inactive')", name='bikes_status_check')
    )
    
    # Create rentals table
    op.create_table('rentals',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_rental_id', sa.Text(), nullable=True),
        sa.Column('bike_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('start_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('end_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('minute_rate_snapshot', sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column('minutes_client', sa.Integer(), nullable=True),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('status', sa.Text(), nullable=False, default='open'),
        sa.Column('path_sample', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['bike_id'], ['bikes.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("status IN ('open','end_pending','closed')", name='rentals_status_check')
    )
    
    # Create payments table
    op.create_table('payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rental_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('method', sa.Text(), nullable=False),
        sa.Column('provider_ref', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), nullable=False, default='pending'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['rental_id'], ['rentals.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("method IN ('mpesa','card','wallet')", name='payments_method_check'),
        sa.CheckConstraint("status IN ('pending','success','failed')", name='payments_status_check')
    )
    
    # Create owner_earnings table
    op.create_table('owner_earnings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('rental_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('owner_share', sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column('cycle_share', sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['rental_id'], ['rentals.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create payouts table
    op.create_table('payouts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('status', sa.Text(), nullable=False, default='requested'),
        sa.Column('requested_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('processed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("status IN ('requested','approved','paid','failed')", name='payouts_status_check')
    )
    
    # Create verification_docs table
    op.create_table('verification_docs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('s3_url', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), nullable=False, default='pending'),
        sa.Column('submitted_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("status IN ('pending','approved','rejected')", name='verification_docs_status_check')
    )
    
    # Create notifications table
    op.create_table('notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('channel', sa.Text(), nullable=True),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('status', sa.Text(), nullable=False, default='pending'),
        sa.Column('sent_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("channel IN ('push','sms','email','in-app')", name='notifications_channel_check'),
        sa.CheckConstraint("status IN ('pending','sent','failed')", name='notifications_status_check')
    )
    
    # Create events table
    op.create_table('events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('bike_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('dock_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('event_type', sa.Text(), nullable=False),
        sa.Column('properties', sa.JSON(), nullable=True),
        sa.Column('occurred_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['bike_id'], ['bikes.id'], ),
        sa.ForeignKeyConstraint(['dock_id'], ['docks.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create admin_policies table
    op.create_table('admin_policies',
        sa.Column('key', sa.Text(), nullable=False),
        sa.Column('value', sa.JSON(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('key')
    )
    
    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.Text(), nullable=False),
        sa.Column('target_type', sa.Text(), nullable=True),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Insert default admin policies
    op.execute("""
        INSERT INTO admin_policies (key, value) VALUES
        ('owner_max_bikes_default', '{"value": 1}'),
        ('hourly_rate_min', '{"value": 50}'),
        ('hourly_rate_max', '{"value": 70}'),
        ('eco_points_redeem_threshold', '{"value": 1000}'),
        ('eco_points_coupon_pct', '{"value": 20}')
        ON CONFLICT (key) DO NOTHING
    """)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('audit_logs')
    op.drop_table('admin_policies')
    op.drop_table('events')
    op.drop_table('notifications')
    op.drop_table('verification_docs')
    op.drop_table('payouts')
    op.drop_table('owner_earnings')
    op.drop_table('payments')
    op.drop_table('rentals')
    op.drop_table('bikes')
    op.drop_table('zones')
    op.drop_table('docks')
    op.drop_table('devices')
    op.drop_table('users')
    
    # Drop PostGIS extension
    op.execute('DROP EXTENSION IF EXISTS postgis')
