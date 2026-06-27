"""Allow multiple PLUs to share the same 8-digit item_code

Revision ID: 004_shared_item_codes
Revises: 003_p_items_shred
Create Date: 2026-06-28
"""

from typing import Sequence, Union

from alembic import op

revision: str = "004_shared_item_codes"
down_revision: Union[str, None] = "003_p_items_shred"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("item_code", "item_master", type_="unique")


def downgrade() -> None:
    op.create_unique_constraint("item_code", "item_master", ["item_code"])
