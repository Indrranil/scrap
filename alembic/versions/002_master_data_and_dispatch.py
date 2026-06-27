"""Master data tables and dispatch enhancements

Revision ID: 002_master_data
Revises: 001_initial
Create Date: 2026-06-27
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_master_data"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "item_master",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("plu_code", sa.String(length=20), nullable=False),
        sa.Column("item_code", sa.String(length=20), nullable=True),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("uom", sa.String(length=10), nullable=False),
        sa.Column("is_shreddable", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("updated_at", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("plu_code"),
        sa.UniqueConstraint("item_code"),
    )
    op.create_index("ix_item_master_plu_code", "item_master", ["plu_code"])
    op.create_index("ix_item_master_item_code", "item_master", ["item_code"])
    op.create_index("ix_item_master_name", "item_master", ["name"])

    op.create_table(
        "vendor",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_vendor_name", "vendor", ["name"])

    op.create_table(
        "vendor_item",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("rate_inr", sa.Numeric(12, 2), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["item_master.id"]),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendor.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vendor_id", "item_id", name="uq_vendor_item"),
    )
    op.create_index("ix_vendor_item_vendor_id", "vendor_item", ["vendor_id"])
    op.create_index("ix_vendor_item_item_id", "vendor_item", ["item_id"])

    # Backfill plu_code from existing item_code before schema changes
    op.add_column("transfer", sa.Column("plu_code", sa.String(length=20), nullable=True))
    op.execute("UPDATE transfer SET plu_code = item_code WHERE plu_code IS NULL")
    op.create_index("ix_transfer_plu_code", "transfer", ["plu_code"])

    op.add_column(
        "transfer",
        sa.Column("item_master_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_transfer_item_master_id",
        "transfer",
        "item_master",
        ["item_master_id"],
        ["id"],
    )
    op.create_index("ix_transfer_item_master_id", "transfer", ["item_master_id"])

    op.add_column(
        "transfer",
        sa.Column(
            "dispatch_method",
            sa.String(length=10),
            nullable=False,
            server_default="qr",
        ),
    )
    op.add_column(
        "transfer",
        sa.Column(
            "material_state",
            sa.String(length=20),
            nullable=False,
            server_default="not_shredded",
        ),
    )

    op.alter_column("transfer", "qr_raw", existing_type=sa.String(length=2000), nullable=True)

    op.drop_column("transfer", "gp_number")
    op.drop_column("transfer", "gr_number")


def downgrade() -> None:
    op.add_column(
        "transfer",
        sa.Column("gr_number", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "transfer",
        sa.Column("gp_number", sa.String(length=100), nullable=True),
    )

    op.alter_column("transfer", "qr_raw", existing_type=sa.String(length=2000), nullable=False)

    op.drop_column("transfer", "material_state")
    op.drop_column("transfer", "dispatch_method")

    op.drop_constraint("fk_transfer_item_master_id", "transfer", type_="foreignkey")
    op.drop_index("ix_transfer_item_master_id", table_name="transfer")
    op.drop_column("transfer", "item_master_id")

    op.drop_index("ix_transfer_plu_code", table_name="transfer")
    op.drop_column("transfer", "plu_code")

    op.drop_table("vendor_item")
    op.drop_table("vendor")
    op.drop_table("item_master")
