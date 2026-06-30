"""Shred pre/post quantities, security entity, GSO plant scoping

Revision ID: 008_shred_security_gso_plant
Revises: 007_inventory_and_sales
Create Date: 2026-06-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "008_shred_security_gso_plant"
down_revision: Union[str, None] = "007_inventory_and_sales"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_QUANTITY_TYPE = sa.Numeric(12, 3)


def _insp():
    return inspect(op.get_bind())


def _columns(table: str) -> set[str]:
    return {c["name"] for c in _insp().get_columns(table)}


def _has_table(table: str) -> bool:
    return table in _insp().get_table_names()


def _has_index(table: str, index_name: str) -> bool:
    return any(i["name"] == index_name for i in _insp().get_indexes(table))


def _has_fk(table: str, fk_name: str) -> bool:
    return any(fk["name"] == fk_name for fk in _insp().get_foreign_keys(table))


def _upgrade_shred_log() -> None:
    cols = _columns("shred_log")

    if "quantity_pre_shred" not in cols:
        op.add_column(
            "shred_log",
            sa.Column("quantity_pre_shred", _QUANTITY_TYPE, nullable=True),
        )
        cols.add("quantity_pre_shred")

    if "quantity_post_shred" not in cols:
        op.add_column(
            "shred_log",
            sa.Column("quantity_post_shred", _QUANTITY_TYPE, nullable=True),
        )
        cols.add("quantity_post_shred")

    if "quantity_kg" in cols:
        op.execute(
            "UPDATE shred_log SET quantity_post_shred = quantity_kg, "
            "quantity_pre_shred = quantity_kg WHERE quantity_kg IS NOT NULL"
        )

    # Re-read nullable flags after partial runs.
    col_meta = {c["name"]: c for c in _insp().get_columns("shred_log")}
    if col_meta["quantity_pre_shred"].get("nullable", True):
        op.alter_column(
            "shred_log",
            "quantity_pre_shred",
            existing_type=_QUANTITY_TYPE,
            nullable=False,
        )
    if col_meta["quantity_post_shred"].get("nullable", True):
        op.alter_column(
            "shred_log",
            "quantity_post_shred",
            existing_type=_QUANTITY_TYPE,
            nullable=False,
        )

    if "quantity_kg" in _columns("shred_log"):
        op.drop_column("shred_log", "quantity_kg")


def _upgrade_security() -> None:
    if not _has_table("security"):
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
    if not _has_index("security", "ix_security_login_id"):
        op.create_index("ix_security_login_id", "security", ["login_id"])

    if "security_id" not in _columns("employee_profile"):
        op.add_column(
            "employee_profile",
            sa.Column("security_id", sa.Integer(), nullable=True),
        )
    if not _has_fk("employee_profile", "fk_employee_profile_security_id"):
        op.create_foreign_key(
            "fk_employee_profile_security_id",
            "employee_profile",
            "security",
            ["security_id"],
            ["id"],
        )
    if not _has_index("employee_profile", "ix_employee_profile_security_id"):
        op.create_index(
            "ix_employee_profile_security_id",
            "employee_profile",
            ["security_id"],
        )


def _upgrade_gso_plant() -> None:
    if "plant_id" not in _columns("gso"):
        op.add_column("gso", sa.Column("plant_id", sa.Integer(), nullable=True))
    if not _has_fk("gso", "fk_gso_plant_id"):
        op.create_foreign_key(
            "fk_gso_plant_id", "gso", "plant", ["plant_id"], ["id"]
        )
    if not _has_index("gso", "ix_gso_plant_id"):
        op.create_index("ix_gso_plant_id", "gso", ["plant_id"], unique=True)


def upgrade() -> None:
    _upgrade_shred_log()
    _upgrade_security()
    _upgrade_gso_plant()


def downgrade() -> None:
    if _has_index("gso", "ix_gso_plant_id"):
        op.drop_index("ix_gso_plant_id", table_name="gso")
    if _has_fk("gso", "fk_gso_plant_id"):
        op.drop_constraint("fk_gso_plant_id", "gso", type_="foreignkey")
    if "plant_id" in _columns("gso"):
        op.drop_column("gso", "plant_id")

    if _has_index("employee_profile", "ix_employee_profile_security_id"):
        op.drop_index(
            "ix_employee_profile_security_id", table_name="employee_profile"
        )
    if _has_fk("employee_profile", "fk_employee_profile_security_id"):
        op.drop_constraint(
            "fk_employee_profile_security_id",
            "employee_profile",
            type_="foreignkey",
        )
    if "security_id" in _columns("employee_profile"):
        op.drop_column("employee_profile", "security_id")

    if _has_index("security", "ix_security_login_id"):
        op.drop_index("ix_security_login_id", table_name="security")
    if _has_table("security"):
        op.drop_table("security")

    cols = _columns("shred_log")
    if "quantity_kg" not in cols:
        op.add_column(
            "shred_log",
            sa.Column("quantity_kg", _QUANTITY_TYPE, nullable=True),
        )
        if "quantity_post_shred" in cols:
            op.execute(
                "UPDATE shred_log SET quantity_kg = quantity_post_shred "
                "WHERE quantity_post_shred IS NOT NULL"
            )
        col_meta = {c["name"]: c for c in _insp().get_columns("shred_log")}
        if col_meta.get("quantity_kg", {}).get("nullable", True):
            op.alter_column(
                "shred_log",
                "quantity_kg",
                existing_type=_QUANTITY_TYPE,
                nullable=False,
            )

    if "quantity_post_shred" in _columns("shred_log"):
        op.drop_column("shred_log", "quantity_post_shred")
    if "quantity_pre_shred" in _columns("shred_log"):
        op.drop_column("shred_log", "quantity_pre_shred")
