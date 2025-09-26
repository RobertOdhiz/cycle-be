"""Add reset_token fields to User

Revision ID: 1bdeec9632d7
Revises: 3a4ae1ea0c8b
Create Date: 2025-09-24 19:48:02.131719

"""
from alembic import op
import sqlalchemy as sa

revision = 'your_new_revision_id'
down_revision = '3a4ae1ea0c8b'  # Your previous revision
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Only add the two required columns
    op.add_column('users', sa.Column('reset_token', sa.String(), nullable=True))
    op.add_column('users', sa.Column('reset_token_expires', sa.DateTime(), nullable=True))

def downgrade() -> None:
    op.drop_column('users', 'reset_token_expires')
    op.drop_column('users', 'reset_token')