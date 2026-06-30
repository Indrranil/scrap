import time
from decimal import Decimal
from typing import List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.enums import InventoryMovementType
from app.models.inventory_movement import InventoryMovement
from app.models.material_inventory import MaterialInventory
from app.schemas.shred import ReadyForSaleItem


class InventoryService:
    def _get_or_create_row(
        self,
        db: Session,
        scrapeyard_id: int,
        item_code: str,
        item_name: str,
        uom: str,
    ) -> MaterialInventory:
        row = (
            db.query(MaterialInventory)
            .filter(
                MaterialInventory.scrapeyard_id == scrapeyard_id,
                MaterialInventory.item_code == item_code,
            )
            .first()
        )
        if row:
            return row
        now = int(time.time())
        row = MaterialInventory(
            scrapeyard_id=scrapeyard_id,
            item_code=item_code,
            item_name=item_name,
            uom=uom,
            quantity_available=Decimal("0"),
            updated_at=now,
        )
        db.add(row)
        db.flush()
        return row

    def _record_movement(
        self,
        db: Session,
        scrapeyard_id: int,
        item_code: str,
        movement_type: InventoryMovementType,
        quantity_delta: Decimal,
        reference_type: Optional[str],
        reference_id: Optional[int],
    ) -> None:
        db.add(
            InventoryMovement(
                scrapeyard_id=scrapeyard_id,
                item_code=item_code,
                movement_type=movement_type.value,
                quantity_delta=quantity_delta,
                reference_type=reference_type,
                reference_id=reference_id,
                created_at=int(time.time()),
            )
        )

    def add_stock(
        self,
        db: Session,
        scrapeyard_id: int,
        item_code: str,
        item_name: str,
        uom: str,
        quantity: Decimal,
        movement_type: InventoryMovementType,
        reference_type: str,
        reference_id: int,
    ) -> MaterialInventory:
        if quantity <= 0:
            raise HTTPException(status_code=422, detail="Quantity must be positive")
        row = self._get_or_create_row(db, scrapeyard_id, item_code, item_name, uom)
        row.quantity_available += quantity
        row.item_name = item_name
        row.uom = uom
        row.updated_at = int(time.time())
        self._record_movement(
            db,
            scrapeyard_id,
            item_code,
            movement_type,
            quantity,
            reference_type,
            reference_id,
        )
        return row

    def reserve_stock(
        self,
        db: Session,
        scrapeyard_id: int,
        item_code: str,
        quantity: Decimal,
        reference_type: str,
        reference_id: int,
    ) -> MaterialInventory:
        row = (
            db.query(MaterialInventory)
            .filter(
                MaterialInventory.scrapeyard_id == scrapeyard_id,
                MaterialInventory.item_code == item_code,
            )
            .with_for_update()
            .first()
        )
        if not row or row.quantity_available < quantity:
            raise HTTPException(
                status_code=422,
                detail="Insufficient available quantity for this item",
            )
        row.quantity_available -= quantity
        row.updated_at = int(time.time())
        self._record_movement(
            db,
            scrapeyard_id,
            item_code,
            InventoryMovementType.SALE_RESERVE,
            -quantity,
            reference_type,
            reference_id,
        )
        return row

    def release_stock(
        self,
        db: Session,
        scrapeyard_id: int,
        item_code: str,
        item_name: str,
        uom: str,
        quantity: Decimal,
        reference_type: str,
        reference_id: int,
    ) -> MaterialInventory:
        row = self._get_or_create_row(
            db, scrapeyard_id, item_code, item_name, uom
        )
        row.quantity_available += quantity
        row.updated_at = int(time.time())
        self._record_movement(
            db,
            scrapeyard_id,
            item_code,
            InventoryMovementType.SALE_RELEASE,
            quantity,
            reference_type,
            reference_id,
        )
        return row

    def get_available(
        self,
        db: Session,
        scrapeyard_id: int,
        *,
        item_code: Optional[str] = None,
        material_name: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[int, List[ReadyForSaleItem]]:
        query = db.query(MaterialInventory).filter(
            MaterialInventory.scrapeyard_id == scrapeyard_id,
            MaterialInventory.quantity_available > 0,
        )
        if item_code:
            query = query.filter(MaterialInventory.item_code.ilike(f"%{item_code}%"))
        if material_name:
            query = query.filter(
                MaterialInventory.item_name.ilike(f"%{material_name}%")
            )
        total = query.count()
        rows = (
            query.order_by(MaterialInventory.item_name.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        items = [
            ReadyForSaleItem(
                item_code=r.item_code,
                material_name=r.item_name,
                available_qty=r.quantity_available,
                uom=r.uom,
            )
            for r in rows
        ]
        return total, items

    def get_stock_quantity(
        self, db: Session, scrapeyard_id: int, item_code: str
    ) -> Decimal:
        row = (
            db.query(MaterialInventory)
            .filter(
                MaterialInventory.scrapeyard_id == scrapeyard_id,
                MaterialInventory.item_code == item_code,
            )
            .first()
        )
        return row.quantity_available if row else Decimal("0")


inventory_service = InventoryService()
