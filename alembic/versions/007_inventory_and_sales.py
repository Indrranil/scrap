"""Material inventory ledger and material_sale

Revision ID: 007_inventory_and_sales
Revises: 006_vendor_profile
Create Date: 2026-06-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007_inventory_and_sales"
down_revision: Union[str, None] = "006_vendor_profile"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "material_inventory",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("scrapeyard_id", sa.Integer(), nullable=False),
        sa.Column("item_code", sa.String(length=20), nullable=False),
        sa.Column("item_name", sa.String(length=500), nullable=False),
        sa.Column("uom", sa.String(length=10), nullable=False),
        sa.Column("quantity_available", sa.Numeric(12, 3), nullable=False),
        sa.Column("updated_at", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(["scrapeyard_id"], ["scrapeyard.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scrapeyard_id", "item_code", name="uq_inventory_scrapeyard_item"),
    )
    op.create_index(
        "ix_material_inventory_scrapeyard_id", "material_inventory", ["scrapeyard_id"]
    )
    op.create_index(
        "ix_material_inventory_item_code", "material_inventory", ["item_code"]
    )

    op.create_table(
        "inventory_movement",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("scrapeyard_id", sa.Integer(), nullable=False),
        sa.Column("item_code", sa.String(length=20), nullable=False),
        sa.Column("movement_type", sa.String(length=30), nullable=False),
        sa.Column("quantity_delta", sa.Numeric(12, 3), nullable=False),
        sa.Column("reference_type", sa.String(length=30), nullable=True),
        sa.Column("reference_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(["scrapeyard_id"], ["scrapeyard.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_inventory_movement_scrapeyard_id", "inventory_movement", ["scrapeyard_id"]
    )

    op.create_table(
        "material_sale",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("scrapeyard_id", sa.Integer(), nullable=False),
        sa.Column("item_code", sa.String(length=20), nullable=False),
        sa.Column("item_name", sa.String(length=500), nullable=False),
        sa.Column("uom", sa.String(length=10), nullable=False),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("vehicle_number", sa.String(length=50), nullable=False),
        sa.Column("quantity_sold", sa.Numeric(12, 3), nullable=False),
        sa.Column("total_weight_kg", sa.Numeric(12, 3), nullable=True),
        sa.Column("amount_inr", sa.Numeric(14, 2), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("recorded_by", sa.Integer(), nullable=False),
        sa.Column("recorded_at", sa.BigInteger(), nullable=False),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.BigInteger(), nullable=True),
        sa.Column("rejection_comment", sa.Text(), nullable=True),
        sa.Column("transfer_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["scrapeyard_id"], ["scrapeyard.id"]),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendor.id"]),
        sa.ForeignKeyConstraint(["recorded_by"], ["employee_profile.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["employee_profile.id"]),
        sa.ForeignKeyConstraint(["transfer_id"], ["transfer.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_material_sale_scrapeyard_id", "material_sale", ["scrapeyard_id"])
    op.create_index("ix_material_sale_item_code", "material_sale", ["item_code"])
    op.create_index("ix_material_sale_status", "material_sale", ["status"])
    op.create_index("ix_material_sale_recorded_at", "material_sale", ["recorded_at"])


def downgrade() -> None:
    op.drop_index("ix_material_sale_recorded_at", table_name="material_sale")
    op.drop_index("ix_material_sale_status", table_name="material_sale")
    op.drop_index("ix_material_sale_item_code", table_name="material_sale")
    op.drop_index("ix_material_sale_scrapeyard_id", table_name="material_sale")
    op.drop_table("material_sale")

    op.drop_index("ix_inventory_movement_scrapeyard_id", table_name="inventory_movement")
    op.drop_table("inventory_movement")

    op.drop_index("ix_material_inventory_item_code", table_name="material_inventory")
    op.drop_index("ix_material_inventory_scrapeyard_id", table_name="material_inventory")
    op.drop_table("material_inventory")
