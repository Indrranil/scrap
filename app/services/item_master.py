import time
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.constants.items import SHREDDABLE_PLU_CODES
from app.models.item_master import ItemMaster
from app.schemas.item import ItemMasterCreate, ItemMasterResponse, ItemMasterUpdate


def normalize_plu_code(value: str) -> str:
    value = value.strip().upper()
    if value.isdigit():
        return str(int(value))
    return value


class ItemMasterService:
    def _to_response(self, item: ItemMaster) -> ItemMasterResponse:
        return ItemMasterResponse.model_validate(item)

    def get_by_plu_code(self, db: Session, plu_code: str) -> Optional[ItemMaster]:
        normalized = normalize_plu_code(plu_code)
        return (
            db.query(ItemMaster)
            .filter(
                ItemMaster.plu_code == normalized,
                ItemMaster.is_active.is_(True),
            )
            .first()
        )

    def get_by_id(self, db: Session, item_id: int) -> ItemMaster:
        item = (
            db.query(ItemMaster)
            .filter(ItemMaster.id == item_id, ItemMaster.is_active.is_(True))
            .first()
        )
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        return item

    def list_items(
        self,
        db: Session,
        *,
        search: Optional[str] = None,
        uom: Optional[str] = None,
        is_shreddable: Optional[bool] = None,
        is_active: Optional[bool] = True,
        skip: int = 0,
        limit: int = 200,
    ) -> tuple[int, List[ItemMasterResponse]]:
        query = db.query(ItemMaster)
        if is_active is not None:
            query = query.filter(ItemMaster.is_active.is_(is_active))
        if uom:
            query = query.filter(ItemMaster.uom.ilike(uom))
        if is_shreddable is not None:
            query = query.filter(ItemMaster.is_shreddable.is_(is_shreddable))
        if search:
            like = f"%{search}%"
            query = query.filter(
                (ItemMaster.name.ilike(like))
                | (ItemMaster.plu_code.ilike(like))
                | (ItemMaster.item_code.ilike(like))
            )
        total = query.count()
        items = (
            query.order_by(ItemMaster.name.asc()).offset(skip).limit(limit).all()
        )
        return total, [self._to_response(i) for i in items]

    def create_item(self, db: Session, data: ItemMasterCreate) -> ItemMasterResponse:
        plu_code = normalize_plu_code(data.plu_code)
        if db.query(ItemMaster).filter(ItemMaster.plu_code == plu_code).first():
            raise HTTPException(status_code=409, detail="PLU code already exists")
        if data.item_code:
            if (
                db.query(ItemMaster)
                .filter(ItemMaster.item_code == data.item_code)
                .first()
            ):
                raise HTTPException(status_code=409, detail="Item code already exists")

        now = int(time.time())
        item = ItemMaster(
            plu_code=plu_code,
            item_code=data.item_code,
            name=data.name.strip(),
            uom=data.uom.upper(),
            is_shreddable=data.is_shreddable or plu_code in SHREDDABLE_PLU_CODES,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return self._to_response(item)

    def update_item(
        self, db: Session, item_id: int, data: ItemMasterUpdate
    ) -> ItemMasterResponse:
        item = db.query(ItemMaster).filter(ItemMaster.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        if data.plu_code is not None:
            plu_code = normalize_plu_code(data.plu_code)
            existing = (
                db.query(ItemMaster)
                .filter(ItemMaster.plu_code == plu_code, ItemMaster.id != item_id)
                .first()
            )
            if existing:
                raise HTTPException(status_code=409, detail="PLU code already exists")
            item.plu_code = plu_code
        if data.item_code is not None:
            if data.item_code:
                existing = (
                    db.query(ItemMaster)
                    .filter(
                        ItemMaster.item_code == data.item_code,
                        ItemMaster.id != item_id,
                    )
                    .first()
                )
                if existing:
                    raise HTTPException(
                        status_code=409, detail="Item code already exists"
                    )
            item.item_code = data.item_code or None
        if data.name is not None:
            item.name = data.name.strip()
        if data.uom is not None:
            item.uom = data.uom.upper()
        if data.is_shreddable is not None:
            item.is_shreddable = data.is_shreddable
        if data.is_active is not None:
            item.is_active = data.is_active
        item.updated_at = int(time.time())
        db.commit()
        db.refresh(item)
        return self._to_response(item)

    def delete_item(self, db: Session, item_id: int) -> ItemMasterResponse:
        item = db.query(ItemMaster).filter(ItemMaster.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        item.is_active = False
        item.updated_at = int(time.time())
        db.commit()
        db.refresh(item)
        return self._to_response(item)


item_master_service = ItemMasterService()
