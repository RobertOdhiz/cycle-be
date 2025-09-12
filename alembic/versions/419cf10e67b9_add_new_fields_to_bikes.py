"""Add new fields to bikes

Revision ID: 419cf10e67b9
Revises: 9bc8600d34eb
Create Date: 2025-09-04 17:14:50.970709
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "419cf10e67b9"
down_revision = "9bc8600d34eb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bikes", sa.Column("locked", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("bikes", sa.Column("locked_at", sa.DateTime(), nullable=True))
    op.add_column("bikes", sa.Column("unlocked_at", sa.DateTime(), nullable=True))
    op.add_column("bikes", sa.Column("rented_at", sa.DateTime(), nullable=True))
    op.add_column("bikes", sa.Column("returned_at", sa.DateTime(), nullable=True))
    op.add_column("bikes", sa.Column("available_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("bikes", "available_at")
    op.drop_column("bikes", "returned_at")
    op.drop_column("bikes", "rented_at")
    op.drop_column("bikes", "unlocked_at")
    op.drop_column("bikes", "locked_at")
    op.drop_column("bikes", "locked")
