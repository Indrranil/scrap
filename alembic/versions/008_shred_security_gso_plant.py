"""Shred pre/post quantities, security entity, GSO plant scoping

Revision ID: 008_shred_security_gso_plant
Revises: 007_inventory_and_sales
Create Date: 2026-06-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008_shred_security_gso_plant"
down_revision: Union[str, None] = "007_inventory_and_sales"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "shred_log",
        sa.Column("quantity_pre_shred", sa.Numeric(12, 3), nullable=True),
    )
    op.add_column(
        "shred_log",
        sa.Column("quantity_post_shred", sa.Numeric(12, 3), nullable=True),
    )
    op.execute(
        "UPDATE shred_log SET quantity_post_shred = quantity_kg, "
        "quantity_pre_shred = quantity_kg WHERE quantity_kg IS NOT NULL"
    )
    op.alter_column("shred_log", "quantity_pre_shred", nullable=False)
    op.alter_column("shred_log", "quantity_post_shred", nullable=False)
    op.drop_column("shred_log", "quantity_kg")

    op.create_table(
        "security",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("login_id", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("login_id"),
    )
    op.create_index("ix_security_login_id", "security", ["login_id"])

    op.add_column(
        "employee_profile", sa.Column("security_id", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        "fk_employee_profile_security_id",
        "employee_profile",
        "security",
        ["security_id"],
        ["id"],
    )
    op.create_index(
        "ix_employee_profile_security_id", "employee_profile", ["security_id"]
    )

    op.add_column("gso", sa.Column("plant_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_gso_plant_id", "gso", "plant", ["plant_id"], ["id"]
    )
    op.create_index("ix_gso_plant_id", "gso", ["plant_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_gso_plant_id", table_name="gso")
    op.drop_constraint("fk_gso_plant_id", "gso", type_="foreignkey")
    op.drop_column("gso", "plant_id")

    op.drop_index("ix_employee_profile_security_id", table_name="employee_profile")
    op.drop_constraint(
        "fk_employee_profile_security_id", "employee_profile", type_="foreignkey"
    )
    op.drop_column("employee_profile", "security_id")

    op.drop_index("ix_security_login_id", table_name="security")
    op.drop_table("security")

    op.add_column(
        "shred_log",
        sa.Column("quantity_kg", sa.Numeric(12, 3), nullable=True),
    )
    op.execute(
        "UPDATE shred_log SET quantity_kg = quantity_post_shred "
        "WHERE quantity_post_shred IS NOT NULL"
    )
    op.alter_column("shred_log", "quantity_kg", nullable=False)
    op.drop_column("shred_log", "quantity_post_shred")
    op.drop_column("shred_log", "quantity_pre_shred")
