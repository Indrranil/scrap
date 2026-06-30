import time
from decimal import Decimal
from typing import List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import validate_scrapeyard_employee, validate_security_employee
from app.models.enums import InventoryMovementType, MaterialSaleStatus, TransferStatus
from app.models.item_master import ItemMaster
from app.models.material_inventory import MaterialInventory
from app.models.material_sale import MaterialSale
from app.models.shred_log import ShredLog
from app.models.transfer import Transfer
from app.models.vendor import Vendor
from app.models.vendor_item import VendorItem
from app.schemas.material_sale import (
    MaterialSaleEventResponse,
    MaterialSaleListItem,
    MaterialSaleResponse,
)
from app.schemas.shred import ShredLogResponse, ShredQueueItem, ShredSaveRequest
from app.services.inventory import inventory_service
from app.services.status_display import compute_sale_display_status


class ShredService:
    def _to_response(self, log: ShredLog) -> ShredLogResponse:
        return ShredLogResponse(
            id=log.id,
            transfer_id=log.transfer_id,
            scrapeyard_id=log.scrapeyard_id,
            input_plu_code=log.input_plu_code,
            input_name=log.input_name,
            output_item_code=log.output_item_code,
            output_name=log.output_name,
            quantity_pre_shred=log.quantity_pre_shred,
            quantity_post_shred=log.quantity_post_shred,
            process_loss=log.quantity_pre_shred - log.quantity_post_shred,
            shredded_at=log.shredded_at,
        )

    def save_shred(
        self,
        db: Session,
        scrapeyard_id: int,
        data: ShredSaveRequest,
    ) -> ShredLogResponse:
        employee = validate_scrapeyard_employee(
            db, scrapeyard_id, data.employee_id
        )
        transfer = db.query(Transfer).filter(Transfer.id == data.transfer_id).first()
        if not transfer:
            raise HTTPException(status_code=404, detail="Transfer not found")
        if transfer.status != TransferStatus.ACCEPTED:
            raise HTTPException(
                status_code=400,
                detail="Only accepted transfers can be recorded in shred log",
            )
        if not transfer.is_p_item:
            raise HTTPException(
                status_code=400,
                detail="Shred log is only for P-item transfers",
            )
        if transfer.scrapeyard_id and transfer.scrapeyard_id != scrapeyard_id:
            raise HTTPException(status_code=403, detail="Transfer not for this scrapeyard")

        accepted_qty = transfer.quantity_received or transfer.quantity_sent
        if data.quantity_pre_shred > accepted_qty:
            raise HTTPException(
                status_code=422,
                detail="Pre-shred quantity cannot exceed accepted quantity",
            )
        if data.quantity_post_shred > data.quantity_pre_shred:
            raise HTTPException(
                status_code=422,
                detail="Post-shred quantity cannot exceed pre-shred quantity",
            )

        existing = (
            db.query(ShredLog).filter(ShredLog.transfer_id == transfer.id).first()
        )
        if existing:
            raise HTTPException(
                status_code=409, detail="Shred log already exists for this transfer"
            )

        item = (
            db.query(ItemMaster).filter(ItemMaster.id == transfer.item_master_id).first()
        )
        if not item or not item.shred_output_item_code or not item.shred_output_name:
            raise HTTPException(
                status_code=422,
                detail="P-item has no shred output mapping configured",
            )

        now = int(time.time())
        log = ShredLog(
            transfer_id=transfer.id,
            scrapeyard_id=scrapeyard_id,
            input_plu_code=transfer.plu_code or item.plu_code,
            input_name=transfer.item_name,
            output_item_code=item.shred_output_item_code,
            output_name=item.shred_output_name,
            quantity_pre_shred=data.quantity_pre_shred,
            quantity_post_shred=data.quantity_post_shred,
            shredded_by=employee.id,
            shredded_at=now,
        )
        db.add(log)
        db.flush()

        inventory_service.add_stock(
            db,
            scrapeyard_id,
            item.shred_output_item_code,
            item.shred_output_name,
            transfer.uom,
            data.quantity_post_shred,
            InventoryMovementType.SHRED_OUTPUT,
            "shred_log",
            log.id,
        )
        db.commit()
        db.refresh(log)
        return self._to_response(log)

    def get_shred_log(self, db: Session, log_id: int) -> ShredLogResponse:
        log = db.query(ShredLog).filter(ShredLog.id == log_id).first()
        if not log:
            raise HTTPException(status_code=404, detail="Shred log entry not found")
        return self._to_response(log)

    def list_shred_logs(
        self,
        db: Session,
        *,
        scrapeyard_id: Optional[int] = None,
        item_code: Optional[str] = None,
        material_name: Optional[str] = None,
        output_item_code: Optional[str] = None,
        date_from: Optional[int] = None,
        date_to: Optional[int] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[int, List[ShredLogResponse]]:
        query = db.query(ShredLog)
        if scrapeyard_id:
            query = query.filter(ShredLog.scrapeyard_id == scrapeyard_id)
        code_filter = item_code or output_item_code
        if code_filter:
            query = query.filter(
                (ShredLog.output_item_code.ilike(f"%{code_filter}%"))
                | (ShredLog.input_plu_code.ilike(f"%{code_filter}%"))
            )
        if material_name:
            query = query.filter(
                (ShredLog.output_name.ilike(f"%{material_name}%"))
                | (ShredLog.input_name.ilike(f"%{material_name}%"))
            )
        if date_from:
            query = query.filter(ShredLog.shredded_at >= date_from)
        if date_to:
            query = query.filter(ShredLog.shredded_at <= date_to)

        total = query.count()
        logs = (
            query.order_by(ShredLog.shredded_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return total, [self._to_response(log) for log in logs]

    def list_shred_queue(
        self,
        db: Session,
        scrapeyard_id: int,
        *,
        item_code: Optional[str] = None,
        material_name: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[int, List[ShredQueueItem]]:
        shredded_ids = db.query(ShredLog.transfer_id).subquery()
        query = db.query(Transfer).filter(
            Transfer.scrapeyard_id == scrapeyard_id,
            Transfer.status == TransferStatus.ACCEPTED,
            Transfer.is_p_item.is_(True),
            ~Transfer.id.in_(shredded_ids),
        )
        if item_code:
            query = query.filter(
                (Transfer.item_code.ilike(f"%{item_code}%"))
                | (Transfer.plu_code.ilike(f"%{item_code}%"))
            )
        if material_name:
            query = query.filter(Transfer.item_name.ilike(f"%{material_name}%"))

        total = query.count()
        transfers = (
            query.order_by(Transfer.processed_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        items = [
            ShredQueueItem(
                transfer_id=t.id,
                item_code=t.item_code,
                item_name=t.item_name,
                uom=t.uom,
                available_qty=t.quantity_received or t.quantity_sent,
            )
            for t in transfers
        ]
        return total, items


class MaterialSaleService:
    def _build_events(self, sale: MaterialSale, employee_name: str) -> List[MaterialSaleEventResponse]:
        events = [
            MaterialSaleEventResponse(
                event_type="material_sold",
                actor_role="security",
                employee_name=employee_name,
                quantity=sale.quantity_sold,
                created_at=sale.recorded_at,
            )
        ]
        if sale.reviewed_at and sale.status == MaterialSaleStatus.APPROVED.value:
            events.append(
                MaterialSaleEventResponse(
                    event_type="approved",
                    actor_role="admin",
                    employee_name="Admin",
                    quantity=sale.quantity_sold,
                    created_at=sale.reviewed_at,
                )
            )
        elif sale.reviewed_at and sale.status == MaterialSaleStatus.REJECTED.value:
            events.append(
                MaterialSaleEventResponse(
                    event_type="rejected",
                    actor_role="admin",
                    employee_name="Admin",
                    quantity=sale.quantity_sold,
                    comment=sale.rejection_comment,
                    created_at=sale.reviewed_at,
                )
            )
        return events

    def create_sale(
        self,
        db: Session,
        security_id: int,
        data,
    ) -> MaterialSaleResponse:
        from app.schemas.material_sale import MaterialSaleCreate
        from app.services.scrapeyard import scrapeyard_service

        if not isinstance(data, MaterialSaleCreate):
            raise TypeError("Expected MaterialSaleCreate")

        employee = validate_security_employee(db, security_id, data.employee_id)
        scrapeyard = scrapeyard_service.get_active(db)
        scrapeyard_id = scrapeyard.id
        vendor = (
            db.query(Vendor)
            .filter(Vendor.id == data.vendor_id, Vendor.is_active.is_(True))
            .first()
        )
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")

        inv_row = (
            db.query(MaterialInventory)
            .filter(
                MaterialInventory.scrapeyard_id == scrapeyard_id,
                MaterialInventory.item_code == data.item_code,
            )
            .first()
        )
        if not inv_row:
            raise HTTPException(status_code=404, detail="Item not available for sale")

        available_before = inv_row.quantity_available
        amount_inr = None
        item_master = (
            db.query(ItemMaster)
            .filter(ItemMaster.item_code == data.item_code, ItemMaster.is_active.is_(True))
            .first()
        )
        if item_master:
            vendor_item = (
                db.query(VendorItem)
                .filter(
                    VendorItem.vendor_id == vendor.id,
                    VendorItem.item_id == item_master.id,
                )
                .first()
            )
            if vendor_item:
                amount_inr = vendor_item.rate_inr * data.quantity_sold

        now = int(time.time())
        sale = MaterialSale(
            scrapeyard_id=scrapeyard_id,
            item_code=inv_row.item_code,
            item_name=inv_row.item_name,
            uom=inv_row.uom,
            vendor_id=vendor.id,
            vehicle_number=data.vehicle_number.strip(),
            quantity_sold=data.quantity_sold,
            total_weight_kg=data.total_weight_kg,
            amount_inr=amount_inr,
            status=MaterialSaleStatus.PENDING.value,
            recorded_by=employee.id,
            recorded_at=now,
        )
        db.add(sale)
        db.flush()

        inventory_service.reserve_stock(
            db,
            scrapeyard_id,
            data.item_code,
            data.quantity_sold,
            "material_sale",
            sale.id,
        )
        db.commit()
        db.refresh(sale)

        return MaterialSaleResponse(
            id=sale.id,
            item_code=sale.item_code,
            item_name=sale.item_name,
            uom=sale.uom,
            available_qty_at_sale=available_before,
            quantity_sold=sale.quantity_sold,
            total_weight_kg=sale.total_weight_kg,
            vendor_id=vendor.id,
            vendor_name=vendor.name,
            vehicle_number=sale.vehicle_number,
            amount_inr=sale.amount_inr,
            status=sale.status,
            display_status=compute_sale_display_status(MaterialSaleStatus(sale.status)),
            recorded_at=sale.recorded_at,
            events=self._build_events(sale, employee.name),
        )

    def get_sale(self, db: Session, sale_id: int) -> MaterialSaleResponse:
        sale = db.query(MaterialSale).filter(MaterialSale.id == sale_id).first()
        if not sale:
            raise HTTPException(status_code=404, detail="Sale not found")
        vendor = db.query(Vendor).filter(Vendor.id == sale.vendor_id).first()
        from app.models.employee_profile import EmployeeProfile

        employee = (
            db.query(EmployeeProfile).filter(EmployeeProfile.id == sale.recorded_by).first()
        )
        return MaterialSaleResponse(
            id=sale.id,
            item_code=sale.item_code,
            item_name=sale.item_name,
            uom=sale.uom,
            quantity_sold=sale.quantity_sold,
            total_weight_kg=sale.total_weight_kg,
            vendor_id=sale.vendor_id,
            vendor_name=vendor.name if vendor else "",
            vehicle_number=sale.vehicle_number,
            amount_inr=sale.amount_inr,
            status=sale.status,
            display_status=compute_sale_display_status(MaterialSaleStatus(sale.status)),
            recorded_at=sale.recorded_at,
            events=self._build_events(sale, employee.name if employee else "Unknown"),
        )

    def list_sales(
        self,
        db: Session,
        scrapeyard_id: int,
        *,
        item_code: Optional[str] = None,
        material_name: Optional[str] = None,
        vendor_id: Optional[int] = None,
        status: Optional[str] = None,
        date_from: Optional[int] = None,
        date_to: Optional[int] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[int, List[MaterialSaleListItem]]:
        query = db.query(MaterialSale).filter(MaterialSale.scrapeyard_id == scrapeyard_id)
        if item_code:
            query = query.filter(MaterialSale.item_code.ilike(f"%{item_code}%"))
        if material_name:
            query = query.filter(MaterialSale.item_name.ilike(f"%{material_name}%"))
        if vendor_id:
            query = query.filter(MaterialSale.vendor_id == vendor_id)
        if status:
            query = query.filter(MaterialSale.status == status)
        if date_from:
            query = query.filter(MaterialSale.recorded_at >= date_from)
        if date_to:
            query = query.filter(MaterialSale.recorded_at <= date_to)

        total = query.count()
        sales = (
            query.order_by(MaterialSale.recorded_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        items = []
        for sale in sales:
            vendor = db.query(Vendor).filter(Vendor.id == sale.vendor_id).first()
            items.append(
                MaterialSaleListItem(
                    id=sale.id,
                    item_code=sale.item_code,
                    item_name=sale.item_name,
                    uom=sale.uom,
                    quantity_sold=sale.quantity_sold,
                    vendor_name=vendor.name if vendor else "",
                    status=sale.status,
                    display_status=compute_sale_display_status(
                        MaterialSaleStatus(sale.status)
                    ),
                    recorded_at=sale.recorded_at,
                )
            )
        return total, items

    def approve_sale(
        self, db: Session, sale_id: int, admin_id: int
    ) -> MaterialSaleResponse:
        sale = db.query(MaterialSale).filter(MaterialSale.id == sale_id).first()
        if not sale:
            raise HTTPException(status_code=404, detail="Sale not found")
        if sale.status != MaterialSaleStatus.PENDING.value:
            raise HTTPException(
                status_code=400, detail="Only pending sales can be approved"
            )
        now = int(time.time())
        sale.status = MaterialSaleStatus.APPROVED.value
        sale.reviewed_at = now
        sale.reviewed_by_admin_id = admin_id
        db.commit()
        db.refresh(sale)
        return self.get_sale(db, sale_id)

    def reject_sale(
        self, db: Session, sale_id: int, admin_id: int, reason: str
    ) -> MaterialSaleResponse:
        sale = db.query(MaterialSale).filter(MaterialSale.id == sale_id).first()
        if not sale:
            raise HTTPException(status_code=404, detail="Sale not found")
        if sale.status != MaterialSaleStatus.PENDING.value:
            raise HTTPException(
                status_code=400, detail="Only pending sales can be rejected"
            )
        now = int(time.time())
        sale.status = MaterialSaleStatus.REJECTED.value
        sale.rejection_comment = reason.strip()
        sale.reviewed_at = now
        sale.reviewed_by_admin_id = admin_id
        self.release_sale_stock(db, sale_id)
        db.commit()
        db.refresh(sale)
        return self.get_sale(db, sale_id)

    def release_sale_stock(self, db: Session, sale_id: int) -> None:
        """Restore inventory when admin rejects a sale (admin phase hook)."""
        sale = db.query(MaterialSale).filter(MaterialSale.id == sale_id).first()
        if not sale:
            raise HTTPException(status_code=404, detail="Sale not found")
        inventory_service.release_stock(
            db,
            sale.scrapeyard_id,
            sale.item_code,
            sale.item_name,
            sale.uom,
            sale.quantity_sold,
            "material_sale",
            sale.id,
        )


shred_service = ShredService()
material_sale_service = MaterialSaleService()
