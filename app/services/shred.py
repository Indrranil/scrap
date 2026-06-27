import time
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import validate_scrapeyard_employee
from app.models.enums import TransferStatus
from app.models.item_master import ItemMaster
from app.models.shred_log import ShredLog
from app.models.transfer import Transfer
from app.schemas.shred import ShredLogResponse, ShredSaveRequest


class ShredService:
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
            quantity_kg=data.quantity_kg,
            shredded_by=employee.id,
            shredded_at=now,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return ShredLogResponse.model_validate(log)

    def get_shred_log(self, db: Session, log_id: int) -> ShredLogResponse:
        log = db.query(ShredLog).filter(ShredLog.id == log_id).first()
        if not log:
            raise HTTPException(status_code=404, detail="Shred log entry not found")
        return ShredLogResponse.model_validate(log)

    def list_shred_logs(
        self,
        db: Session,
        *,
        scrapeyard_id: Optional[int] = None,
        output_item_code: Optional[str] = None,
        date_from: Optional[int] = None,
        date_to: Optional[int] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[int, List[ShredLogResponse]]:
        query = db.query(ShredLog)
        if scrapeyard_id:
            query = query.filter(ShredLog.scrapeyard_id == scrapeyard_id)
        if output_item_code:
            query = query.filter(
                ShredLog.output_item_code.ilike(f"%{output_item_code}%")
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
        return total, [ShredLogResponse.model_validate(log) for log in logs]


shred_service = ShredService()
