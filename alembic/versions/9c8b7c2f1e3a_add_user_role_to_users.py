"""add user role to users

Revision ID: 9c8b7c2f1e3a
Revises: 9bc8600d34eb
Create Date: 2025-09-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c8b7c2f1e3a'
down_revision: Union[str, None] = '9bc8600d34eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum type
    userrole_enum = sa.Enum('user', 'staff', 'admin', name='userrole_enum')
    userrole_enum.create(op.get_bind(), checkfirst=True)

    # Add column with default 'user' (server default ensures existing rows have a value)
    op.add_column('users', sa.Column('role', userrole_enum, nullable=False, server_default='user'))

    # Backfill existing rows explicitly (for safety)
    op.execute("UPDATE users SET role = 'user' WHERE role IS NULL")

    # Optionally drop server default to avoid locking in default at DB level (app has default)
    op.alter_column('users', 'role', server_default=None)


def downgrade() -> None:
    # Drop column then enum type
    op.drop_column('users', 'role')
    userrole_enum = sa.Enum('user', 'staff', 'admin', name='userrole_enum')
    userrole_enum.drop(op.get_bind(), checkfirst=True)


