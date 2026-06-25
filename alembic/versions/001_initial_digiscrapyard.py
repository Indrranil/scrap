"""Initial DigiScrapyard schema

Revision ID: 001_initial
Revises:
Create Date: 2026-06-25
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "plant",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=50), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("login_id", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("qr_location", sa.Integer(), nullable=False),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("login_id"),
        sa.UniqueConstraint("qr_location"),
    )
    op.create_index("ix_plant_login_id", "plant", ["login_id"])

    op.create_table(
        "scrapeyard",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("login_id", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("login_id"),
    )
    op.create_index("ix_scrapeyard_login_id", "scrapeyard", ["login_id"])

    op.create_table(
        "admin_user",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_index("ix_admin_user_username", "admin_user", ["username"])

    op.create_table(
        "employee_profile",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("plant_id", sa.Integer(), nullable=True),
        sa.Column("scrapeyard_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(["plant_id"], ["plant.id"]),
        sa.ForeignKeyConstraint(["scrapeyard_id"], ["scrapeyard.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_employee_profile_plant_id", "employee_profile", ["plant_id"])
    op.create_index(
        "ix_employee_profile_scrapeyard_id", "employee_profile", ["scrapeyard_id"]
    )

    op.create_table(
        "transfer",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("qr_raw", sa.String(length=2000), nullable=False),
        sa.Column("qr_number", sa.String(length=255), nullable=False),
        sa.Column("shopfloor_plant_id", sa.Integer(), nullable=False),
        sa.Column("scrapeyard_id", sa.Integer(), nullable=True),
        sa.Column("item_code", sa.String(length=100), nullable=False),
        sa.Column("item_name", sa.String(length=500), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("uom", sa.String(length=10), nullable=False),
        sa.Column("quantity_sent", sa.Numeric(12, 3), nullable=False),
        sa.Column("quantity_received", sa.Numeric(12, 3), nullable=True),
        sa.Column("gp_number", sa.String(length=100), nullable=True),
        sa.Column("gr_number", sa.String(length=100), nullable=True),
        sa.Column("location", sa.Integer(), nullable=True),
        sa.Column("net_weight", sa.Numeric(12, 3), nullable=True),
        sa.Column("tare_weight", sa.Numeric(12, 3), nullable=True),
        sa.Column("gross_weight", sa.Numeric(12, 3), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("dispatched_by", sa.Integer(), nullable=True),
        sa.Column("dispatched_at", sa.BigInteger(), nullable=True),
        sa.Column("processed_by", sa.Integer(), nullable=True),
        sa.Column("processed_at", sa.BigInteger(), nullable=True),
        sa.Column("acknowledged_by", sa.Integer(), nullable=True),
        sa.Column("acknowledged_at", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(["acknowledged_by"], ["employee_profile.id"]),
        sa.ForeignKeyConstraint(["dispatched_by"], ["employee_profile.id"]),
        sa.ForeignKeyConstraint(["processed_by"], ["employee_profile.id"]),
        sa.ForeignKeyConstraint(["scrapeyard_id"], ["scrapeyard.id"]),
        sa.ForeignKeyConstraint(["shopfloor_plant_id"], ["plant.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("qr_number"),
    )
    op.create_index("ix_transfer_qr_number", "transfer", ["qr_number"])
    op.create_index("ix_transfer_status", "transfer", ["status"])
    op.create_index("ix_transfer_shopfloor_plant_id", "transfer", ["shopfloor_plant_id"])
    op.create_index("ix_transfer_scrapeyard_id", "transfer", ["scrapeyard_id"])
    op.create_index("ix_transfer_item_code", "transfer", ["item_code"])
    op.create_index("ix_transfer_item_name", "transfer", ["item_name"])

    op.create_table(
        "transfer_event",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("transfer_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=20), nullable=False),
        sa.Column("actor_role", sa.String(length=20), nullable=False),
        sa.Column("employee_profile_id", sa.Integer(), nullable=True),
        sa.Column("employee_name", sa.String(length=255), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("photo_path", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(["employee_profile_id"], ["employee_profile.id"]),
        sa.ForeignKeyConstraint(["transfer_id"], ["transfer.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_transfer_event_transfer_id", "transfer_event", ["transfer_id"])
    op.create_index("ix_transfer_event_created_at", "transfer_event", ["created_at"])

    op.create_table(
        "rejection_detail",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("transfer_id", sa.Integer(), nullable=False),
        sa.Column("reason_type", sa.String(length=30), nullable=False),
        sa.Column("qty_received", sa.Numeric(12, 3), nullable=True),
        sa.Column("material_received_name", sa.String(length=500), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["transfer_id"], ["transfer.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("transfer_id"),
    )

    op.create_table(
        "scrap_sale",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("transfer_id", sa.Integer(), nullable=False),
        sa.Column("plant_id", sa.Integer(), nullable=False),
        sa.Column("quantity_kg", sa.Numeric(12, 3), nullable=True),
        sa.Column("quantity_ea", sa.Numeric(12, 3), nullable=True),
        sa.Column("amount_inr", sa.Numeric(14, 2), nullable=False),
        sa.Column("sold_at", sa.BigInteger(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["plant_id"], ["plant.id"]),
        sa.ForeignKeyConstraint(["transfer_id"], ["transfer.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scrap_sale_transfer_id", "scrap_sale", ["transfer_id"])
    op.create_index("ix_scrap_sale_plant_id", "scrap_sale", ["plant_id"])


def downgrade() -> None:
    op.drop_table("scrap_sale")
    op.drop_table("rejection_detail")
    op.drop_table("transfer_event")
    op.drop_table("transfer")
    op.drop_table("employee_profile")
    op.drop_table("admin_user")
    op.drop_table("scrapeyard")
    op.drop_table("plant")
