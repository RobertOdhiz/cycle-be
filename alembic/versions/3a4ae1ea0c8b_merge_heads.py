"""merge heads

Revision ID: 3a4ae1ea0c8b
Revises: 419cf10e67b9, 9c8b7c2f1e3a
Create Date: 2025-09-24 17:02:28.780794

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3a4ae1ea0c8b'
down_revision = ('419cf10e67b9', '9c8b7c2f1e3a')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
