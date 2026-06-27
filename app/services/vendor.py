import time
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.item_master import ItemMaster
from app.models.vendor import Vendor
from app.models.vendor_item import VendorItem
from app.schemas.vendor import (
    VendorCreate,
    VendorItemCreate,
    VendorItemResponse,
    VendorItemUpdate,
    VendorResponse,
    VendorUpdate,
)


class VendorService:
    def _to_vendor_response(self, vendor: Vendor) -> VendorResponse:
        return VendorResponse.model_validate(vendor)

    def _to_vendor_item_response(
        self, db: Session, vendor_item: VendorItem
    ) -> VendorItemResponse:
        item = db.query(ItemMaster).filter(ItemMaster.id == vendor_item.item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Linked item not found")
        return VendorItemResponse(
            id=vendor_item.id,
            vendor_id=vendor_item.vendor_id,
            item_id=vendor_item.item_id,
            plu_code=item.plu_code,
            item_code=item.item_code,
            item_name=item.name,
            uom=item.uom,
            rate_inr=vendor_item.rate_inr,
        )

    def list_vendors(
        self, db: Session, search: Optional[str] = None
    ) -> List[VendorResponse]:
        query = db.query(Vendor).filter(Vendor.is_active.is_(True))
        if search:
            query = query.filter(Vendor.name.ilike(f"%{search}%"))
        vendors = query.order_by(Vendor.name.asc()).all()
        return [self._to_vendor_response(v) for v in vendors]

    def get_vendor(self, db: Session, vendor_id: int) -> VendorResponse:
        vendor = (
            db.query(Vendor)
            .filter(Vendor.id == vendor_id, Vendor.is_active.is_(True))
            .first()
        )
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        return self._to_vendor_response(vendor)

    def create_vendor(self, db: Session, data: VendorCreate) -> VendorResponse:
        name = data.name.strip()
        if db.query(Vendor).filter(Vendor.name == name).first():
            raise HTTPException(status_code=409, detail="Vendor already exists")
        vendor = Vendor(
            name=name,
            is_active=True,
            created_at=int(time.time()),
        )
        db.add(vendor)
        db.commit()
        db.refresh(vendor)
        return self._to_vendor_response(vendor)

    def update_vendor(
        self, db: Session, vendor_id: int, data: VendorUpdate
    ) -> VendorResponse:
        vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        if data.name is not None:
            name = data.name.strip()
            existing = (
                db.query(Vendor)
                .filter(Vendor.name == name, Vendor.id != vendor_id)
                .first()
            )
            if existing:
                raise HTTPException(status_code=409, detail="Vendor name already exists")
            vendor.name = name
        if data.is_active is not None:
            vendor.is_active = data.is_active
        db.commit()
        db.refresh(vendor)
        return self._to_vendor_response(vendor)

    def delete_vendor(self, db: Session, vendor_id: int) -> VendorResponse:
        vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        vendor.is_active = False
        db.commit()
        db.refresh(vendor)
        return self._to_vendor_response(vendor)

    def list_vendor_items(
        self, db: Session, vendor_id: int
    ) -> tuple[int, List[VendorItemResponse]]:
        self.get_vendor(db, vendor_id)
        vendor_items = (
            db.query(VendorItem)
            .filter(VendorItem.vendor_id == vendor_id)
            .order_by(VendorItem.id.asc())
            .all()
        )
        items = [self._to_vendor_item_response(db, vi) for vi in vendor_items]
        return len(items), items

    def add_vendor_item(
        self, db: Session, vendor_id: int, data: VendorItemCreate
    ) -> VendorItemResponse:
        self.get_vendor(db, vendor_id)
        item = (
            db.query(ItemMaster)
            .filter(ItemMaster.id == data.item_id, ItemMaster.is_active.is_(True))
            .first()
        )
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        existing = (
            db.query(VendorItem)
            .filter(
                VendorItem.vendor_id == vendor_id,
                VendorItem.item_id == data.item_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=409, detail="Item already assigned to this vendor"
            )
        vendor_item = VendorItem(
            vendor_id=vendor_id,
            item_id=data.item_id,
            rate_inr=data.rate_inr,
        )
        db.add(vendor_item)
        db.commit()
        db.refresh(vendor_item)
        return self._to_vendor_item_response(db, vendor_item)

    def update_vendor_item(
        self, db: Session, vendor_id: int, vendor_item_id: int, data: VendorItemUpdate
    ) -> VendorItemResponse:
        vendor_item = (
            db.query(VendorItem)
            .filter(
                VendorItem.id == vendor_item_id,
                VendorItem.vendor_id == vendor_id,
            )
            .first()
        )
        if not vendor_item:
            raise HTTPException(status_code=404, detail="Vendor item not found")
        vendor_item.rate_inr = data.rate_inr
        db.commit()
        db.refresh(vendor_item)
        return self._to_vendor_item_response(db, vendor_item)

    def remove_vendor_item(
        self, db: Session, vendor_id: int, vendor_item_id: int
    ) -> None:
        vendor_item = (
            db.query(VendorItem)
            .filter(
                VendorItem.id == vendor_item_id,
                VendorItem.vendor_id == vendor_id,
            )
            .first()
        )
        if not vendor_item:
            raise HTTPException(status_code=404, detail="Vendor item not found")
        db.delete(vendor_item)
        db.commit()


vendor_service = VendorService()
