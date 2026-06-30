import time
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.constants.items import SHREDDABLE_PLU_CODES
from app.models.item_master import ItemMaster
from app.models.vendor_item import VendorItem
from app.schemas.item import (
    ItemMasterCreate,
    ItemMasterCreateWithVendors,
    ItemMasterListItem,
    ItemMasterResponse,
    ItemMasterUpdate,
    ItemMasterWithVendorsResponse,
    PostShredOption,
)


def normalize_plu_code(value: str) -> str:
    value = value.strip().upper()
    if value.isdigit():
        return str(int(value))
    return value


class ItemMasterService:
    def _primary_rate(self, db: Session, item_id: int):
        from decimal import Decimal

        row = (
            db.query(VendorItem)
            .filter(VendorItem.item_id == item_id)
            .order_by(VendorItem.id.asc())
            .first()
        )
        return row.rate_inr if row else None

    def _to_list_item(self, db: Session, item: ItemMaster) -> ItemMasterListItem:
        return ItemMasterListItem(
            id=item.id,
            plu_code=item.plu_code,
            item_code=item.item_code,
            name=item.name,
            uom=item.uom,
            is_shreddable=item.is_shreddable,
            is_p_item=item.is_p_item,
            shred_output_name=item.shred_output_name,
            rate_inr=self._primary_rate(db, item.id),
            is_active=item.is_active,
        )

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
        is_p_item: Optional[bool] = None,
        is_active: Optional[bool] = True,
        skip: int = 0,
        limit: int = 200,
    ) -> tuple[int, List[ItemMasterListItem]]:
        query = db.query(ItemMaster)
        if is_active is not None:
            query = query.filter(ItemMaster.is_active.is_(is_active))
        if uom:
            query = query.filter(ItemMaster.uom.ilike(uom))
        if is_shreddable is not None:
            query = query.filter(ItemMaster.is_shreddable.is_(is_shreddable))
        if is_p_item is not None:
            query = query.filter(ItemMaster.is_p_item.is_(is_p_item))
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
        return total, [self._to_list_item(db, i) for i in items]

    def list_post_shred_options(
        self,
        db: Session,
        *,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 200,
    ) -> tuple[int, List[PostShredOption]]:
        query = db.query(ItemMaster).filter(
            ItemMaster.is_active.is_(True),
            ItemMaster.is_p_item.is_(False),
            ItemMaster.item_code.isnot(None),
        )
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
        return total, [
            PostShredOption(
                id=i.id,
                plu_code=i.plu_code,
                item_code=i.item_code,
                name=i.name,
                uom=i.uom,
            )
            for i in items
        ]

    def create_item_with_vendors(
        self, db: Session, data: ItemMasterCreateWithVendors
    ) -> ItemMasterWithVendorsResponse:
        from app.models.vendor import Vendor

        create_data = ItemMasterCreate(**data.model_dump(exclude={"vendors"}))
        plu_code = normalize_plu_code(create_data.plu_code)
        if db.query(ItemMaster).filter(ItemMaster.plu_code == plu_code).first():
            raise HTTPException(status_code=409, detail="PLU code already exists")

        now = int(time.time())
        item = ItemMaster(
            plu_code=plu_code,
            item_code=None if create_data.is_p_item else create_data.item_code,
            name=create_data.name.strip(),
            uom=create_data.uom.upper(),
            is_shreddable=create_data.is_shreddable or plu_code in SHREDDABLE_PLU_CODES,
            is_p_item=create_data.is_p_item,
            shred_output_item_code=create_data.shred_output_item_code,
            shred_output_name=create_data.shred_output_name,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db.add(item)
        db.flush()

        for assignment in data.vendors:
            vendor = (
                db.query(Vendor)
                .filter(Vendor.id == assignment.vendor_id, Vendor.is_active.is_(True))
                .first()
            )
            if not vendor:
                raise HTTPException(
                    status_code=404, detail=f"Vendor {assignment.vendor_id} not found"
                )
            db.add(
                VendorItem(
                    vendor_id=assignment.vendor_id,
                    item_id=item.id,
                    rate_inr=assignment.rate_inr,
                )
            )
        db.commit()
        db.refresh(item)
        return ItemMasterWithVendorsResponse(
            **self._to_response(item).model_dump(),
            vendors=data.vendors,
        )

    def create_item(self, db: Session, data: ItemMasterCreate) -> ItemMasterResponse:
        plu_code = normalize_plu_code(data.plu_code)
        if db.query(ItemMaster).filter(ItemMaster.plu_code == plu_code).first():
            raise HTTPException(status_code=409, detail="PLU code already exists")

        now = int(time.time())
        item = ItemMaster(
            plu_code=plu_code,
            item_code=None if data.is_p_item else data.item_code,
            name=data.name.strip(),
            uom=data.uom.upper(),
            is_shreddable=data.is_shreddable or plu_code in SHREDDABLE_PLU_CODES,
            is_p_item=data.is_p_item,
            shred_output_item_code=data.shred_output_item_code,
            shred_output_name=data.shred_output_name,
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
            item.item_code = data.item_code or None
        if data.name is not None:
            item.name = data.name.strip()
        if data.uom is not None:
            item.uom = data.uom.upper()
        if data.is_shreddable is not None:
            item.is_shreddable = data.is_shreddable
        if data.is_p_item is not None:
            item.is_p_item = data.is_p_item
        if data.shred_output_item_code is not None:
            item.shred_output_item_code = data.shred_output_item_code or None
        if data.shred_output_name is not None:
            item.shred_output_name = data.shred_output_name or None
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
