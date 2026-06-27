import time

from app.constants.items import SHREDDABLE_PLU_CODES
from app.models.item_master import ItemMaster


def seed_test_item(
    db_session,
    *,
    plu_code: str = "1313",
    item_code: str | None = "1000090313",
    name: str = "CORRUGATED BOX SCRAP",
    uom: str = "KG",
    is_shreddable: bool | None = None,
    is_p_item: bool = False,
    shred_output_item_code: str | None = None,
    shred_output_name: str | None = None,
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
        is_p_item=is_p_item,
        shred_output_item_code=shred_output_item_code,
        shred_output_name=shred_output_name,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


def seed_p_item(
    db_session,
    *,
    plu_code: str = "P159",
    name: str = "Cartons",
    shred_output_item_code: str = "1000091259",
    shred_output_name: str = "CARTONS -JT",
) -> ItemMaster:
    return seed_test_item(
        db_session,
        plu_code=plu_code,
        item_code=None,
        name=name,
        is_p_item=True,
        is_shreddable=True,
        shred_output_item_code=shred_output_item_code,
        shred_output_name=shred_output_name,
    )


def seed_ea_item(db_session) -> ItemMaster:
    return seed_test_item(
        db_session,
        plu_code="1021",
        item_code="1000090021",
        name="EMPTY IRON DRUM 200LTR",
        uom="EA",
        is_shreddable=False,
    )
