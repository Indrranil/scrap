"""Vendor profile fields

Revision ID: 006_vendor_profile
Revises: 005_gso_approval
Create Date: 2026-06-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006_vendor_profile"
down_revision: Union[str, None] = "005_gso_approval"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("vendor", sa.Column("vendor_code", sa.String(length=50), nullable=True))
    op.add_column("vendor", sa.Column("email", sa.String(length=255), nullable=True))
    op.add_column(
        "vendor", sa.Column("contact_person", sa.String(length=255), nullable=True)
    )
    op.add_column("vendor", sa.Column("phone", sa.String(length=50), nullable=True))
    op.add_column("vendor", sa.Column("address", sa.String(length=500), nullable=True))
    op.add_column("vendor", sa.Column("gst_number", sa.String(length=50), nullable=True))
    op.add_column("vendor", sa.Column("updated_at", sa.BigInteger(), nullable=True))
    op.create_index("ix_vendor_vendor_code", "vendor", ["vendor_code"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_vendor_vendor_code", table_name="vendor")
    op.drop_column("vendor", "updated_at")
    op.drop_column("vendor", "gst_number")
    op.drop_column("vendor", "address")
    op.drop_column("vendor", "phone")
    op.drop_column("vendor", "contact_person")
    op.drop_column("vendor", "email")
    op.drop_column("vendor", "vendor_code")
