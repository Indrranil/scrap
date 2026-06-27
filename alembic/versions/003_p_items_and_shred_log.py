"""P-items and shred log

Revision ID: 003_p_items_shred
Revises: 002_master_data
Create Date: 2026-06-28
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_p_items_shred"
down_revision: Union[str, None] = "002_master_data"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "item_master",
        sa.Column("is_p_item", sa.Boolean(), nullable=False, server_default="0"),
    )
    op.add_column(
        "item_master",
        sa.Column("shred_output_item_code", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "item_master",
        sa.Column("shred_output_name", sa.String(length=500), nullable=True),
    )

    op.add_column(
        "transfer",
        sa.Column("is_p_item", sa.Boolean(), nullable=False, server_default="0"),
    )

    op.create_table(
        "shred_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("transfer_id", sa.Integer(), nullable=False),
        sa.Column("scrapeyard_id", sa.Integer(), nullable=False),
        sa.Column("input_plu_code", sa.String(length=20), nullable=False),
        sa.Column("input_name", sa.String(length=500), nullable=False),
        sa.Column("output_item_code", sa.String(length=20), nullable=False),
        sa.Column("output_name", sa.String(length=500), nullable=False),
        sa.Column("quantity_kg", sa.Numeric(12, 3), nullable=False),
        sa.Column("shredded_by", sa.Integer(), nullable=False),
        sa.Column("shredded_at", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(["scrapeyard_id"], ["scrapeyard.id"]),
        sa.ForeignKeyConstraint(["shredded_by"], ["employee_profile.id"]),
        sa.ForeignKeyConstraint(["transfer_id"], ["transfer.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("transfer_id"),
    )
    op.create_index("ix_shred_log_transfer_id", "shred_log", ["transfer_id"])
    op.create_index("ix_shred_log_scrapeyard_id", "shred_log", ["scrapeyard_id"])
    op.create_index("ix_shred_log_output_item_code", "shred_log", ["output_item_code"])
    op.create_index("ix_shred_log_shredded_at", "shred_log", ["shredded_at"])


def downgrade() -> None:
    op.drop_table("shred_log")
    op.drop_column("transfer", "is_p_item")
    op.drop_column("item_master", "shred_output_name")
    op.drop_column("item_master", "shred_output_item_code")
    op.drop_column("item_master", "is_p_item")
