"""Add reviewed_by_admin_id to material_sale

Revision ID: 009_admin_material_sale_review
Revises: 008_shred_security_gso_plant
Create Date: 2026-06-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "009_admin_material_sale_review"
down_revision: Union[str, None] = "008_shred_security_gso_plant"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns(table: str) -> set[str]:
    return {c["name"] for c in inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    if "reviewed_by_admin_id" not in _columns("material_sale"):
        op.add_column(
            "material_sale",
            sa.Column("reviewed_by_admin_id", sa.Integer(), nullable=True),
        )
        op.create_foreign_key(
            "fk_material_sale_reviewed_by_admin",
            "material_sale",
            "admin_user",
            ["reviewed_by_admin_id"],
            ["id"],
        )


def downgrade() -> None:
    if "reviewed_by_admin_id" in _columns("material_sale"):
        op.drop_constraint(
            "fk_material_sale_reviewed_by_admin", "material_sale", type_="foreignkey"
        )
        op.drop_column("material_sale", "reviewed_by_admin_id")
