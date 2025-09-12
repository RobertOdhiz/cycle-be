"""Replace s3_url with cloudinary_url in verification_docs

Revision ID: 9bc8600d34eb
Revises: 001
Create Date: 2025-09-01 23:13:45.082946
"""

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision = "9bc8600d34eb"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # add cloudinary_url
    op.add_column("verification_docs", sa.Column("cloudinary_url", sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    # drop s3_url
    op.drop_column("verification_docs", "s3_url")


def downgrade() -> None:
    # restore s3_url
    op.add_column("verification_docs", sa.Column("s3_url", sa.TEXT(), nullable=True))
    # drop cloudinary_url
    op.drop_column("verification_docs", "cloudinary_url")
