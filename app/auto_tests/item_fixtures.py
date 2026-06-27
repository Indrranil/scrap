import time

from app.constants.items import SHREDDABLE_PLU_CODES
from app.models.item_master import ItemMaster


def seed_test_item(
    db_session,
    *,
    plu_code: str = "1313",
    item_code: str = "1000090313",
    name: str = "CORRUGATED BOX SCRAP",
    uom: str = "KG",
    is_shreddable: bool | None = None,
) -> ItemMaster:
    if is_shreddable is None:
        is_shreddable = plu_code in SHREDDABLE_PLU_CODES
    now = int(time.time())
    item = ItemMaster(
        plu_code=plu_code,
        item_code=item_code,
        name=name,
        uom=uom,
        is_shreddable=is_shreddable,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


def seed_ea_item(db_session) -> ItemMaster:
    return seed_test_item(
        db_session,
        plu_code="1021",
        item_code="1000090021",
        name="EMPTY IRON DRUM 200LTR",
        uom="EA",
        is_shreddable=False,
    )
