"""GSO approval gate between shopfloor dispatch and scrapeyard intake

Revision ID: 005_gso_approval
Revises: 004_shared_item_codes
Create Date: 2026-06-28
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005_gso_approval"
down_revision: Union[str, None] = "004_shared_item_codes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "gso",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("login_id", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("login_id"),
    )
    op.create_index("ix_gso_login_id", "gso", ["login_id"])

    op.add_column("employee_profile", sa.Column("gso_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_employee_profile_gso_id", "employee_profile", "gso", ["gso_id"], ["id"]
    )
    op.create_index("ix_employee_profile_gso_id", "employee_profile", ["gso_id"])

    op.add_column(
        "transfer",
        sa.Column("gso_approved_by", sa.Integer(), nullable=True),
    )
    op.add_column(
        "transfer",
        sa.Column("gso_approved_at", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "transfer",
        sa.Column(
            "gso_auto_approved",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "transfer",
        sa.Column("gso_rejected_by", sa.Integer(), nullable=True),
    )
    op.add_column(
        "transfer",
        sa.Column("gso_rejected_at", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "transfer",
        sa.Column("gso_rejection_reason", sa.Text(), nullable=True),
    )
    op.create_foreign_key(
        "fk_transfer_gso_approved_by",
        "transfer",
        "employee_profile",
        ["gso_approved_by"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_transfer_gso_rejected_by",
        "transfer",
        "employee_profile",
        ["gso_rejected_by"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_transfer_gso_rejected_by", "transfer", type_="foreignkey")
    op.drop_constraint("fk_transfer_gso_approved_by", "transfer", type_="foreignkey")
    op.drop_column("transfer", "gso_rejection_reason")
    op.drop_column("transfer", "gso_rejected_at")
    op.drop_column("transfer", "gso_rejected_by")
    op.drop_column("transfer", "gso_auto_approved")
    op.drop_column("transfer", "gso_approved_at")
    op.drop_column("transfer", "gso_approved_by")

    op.drop_index("ix_employee_profile_gso_id", table_name="employee_profile")
    op.drop_constraint("fk_employee_profile_gso_id", "employee_profile", type_="foreignkey")
    op.drop_column("employee_profile", "gso_id")

    op.drop_index("ix_gso_login_id", table_name="gso")
    op.drop_table("gso")
