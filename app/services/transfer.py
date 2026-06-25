import time
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.auth.dependencies import validate_employee
from app.models.employee_profile import EmployeeProfile
from app.models.enums import (
    ActorRole,
    AppRole,
    RejectionReasonType,
    TransferEventType,
    TransferStatus,
)
from app.models.plant import Plant
from app.models.rejection_detail import RejectionDetail
from app.models.transfer import Transfer
from app.models.transfer_event import TransferEvent
from app.schemas.transfer import (
    AcceptRequest,
    DispatchRequest,
    QRScanResponse,
    RejectRequest,
    RejectionDetailResponse,
    TransferEventResponse,
    TransferListItem,
    TransferResponse,
)
from app.services.qr_parser import parse_qr_payload


class TransferService:
    def scan_qr(self, db: Session, qr_raw: str) -> QRScanResponse:
        payload = parse_qr_payload(qr_raw)
        existing = (
            db.query(Transfer).filter(Transfer.qr_number == payload.qr_number).first()
        )
        return QRScanResponse(
            payload=payload,
            existing_transfer_id=existing.id if existing else None,
            existing_status=existing.status if existing else None,
        )

    def _build_response(self, db: Session, transfer: Transfer) -> TransferResponse:
        events = (
            db.query(TransferEvent)
            .filter(TransferEvent.transfer_id == transfer.id)
            .order_by(TransferEvent.created_at.asc())
            .all()
        )
        rejection = (
            db.query(RejectionDetail)
            .filter(RejectionDetail.transfer_id == transfer.id)
            .first()
        )
        return TransferResponse(
            id=transfer.id,
            qr_number=transfer.qr_number,
            item_code=transfer.item_code,
            item_name=transfer.item_name,
            description=transfer.description,
            uom=transfer.uom,
            quantity_sent=transfer.quantity_sent,
            quantity_received=transfer.quantity_received,
            gp_number=transfer.gp_number,
            gr_number=transfer.gr_number,
            location=transfer.location,
            net_weight=transfer.net_weight,
            tare_weight=transfer.tare_weight,
            gross_weight=transfer.gross_weight,
            status=transfer.status,
            dispatched_at=transfer.dispatched_at,
            processed_at=transfer.processed_at,
            acknowledged_at=transfer.acknowledged_at,
            events=[
                TransferEventResponse(
                    id=e.id,
                    event_type=e.event_type,
                    actor_role=e.actor_role.value,
                    employee_name=e.employee_name,
                    quantity=e.quantity,
                    comment=e.comment,
                    photo_path=e.photo_path,
                    created_at=e.created_at,
                )
                for e in events
            ],
            rejection=RejectionDetailResponse.model_validate(rejection)
            if rejection
            else None,
        )

    def get_transfer(self, db: Session, transfer_id: int) -> TransferResponse:
        transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
        if not transfer:
            raise HTTPException(status_code=404, detail="Transfer not found")
        return self._build_response(db, transfer)

    def list_transfers(
        self,
        db: Session,
        *,
        plant_id: Optional[int] = None,
        role: Optional[str] = None,
        item_code: Optional[str] = None,
        material_name: Optional[str] = None,
        status: Optional[TransferStatus] = None,
        date_from: Optional[int] = None,
        date_to: Optional[int] = None,
        rejected_only: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[int, List[TransferListItem]]:
        query = db.query(Transfer)

        if plant_id and role == AppRole.SHOPFLOOR.value:
            query = query.filter(Transfer.shopfloor_plant_id == plant_id)
        elif plant_id and role == AppRole.SCRAPEYARD.value:
            query = query.filter(Transfer.scrapeyard_plant_id == plant_id)

        if item_code:
            query = query.filter(Transfer.item_code.ilike(f"%{item_code}%"))
        if material_name:
            query = query.filter(Transfer.item_name.ilike(f"%{material_name}%"))
        if status:
            query = query.filter(Transfer.status == status)
        if rejected_only:
            query = query.filter(Transfer.status == TransferStatus.REJECTED)
        if date_from:
            query = query.filter(Transfer.dispatched_at >= date_from)
        if date_to:
            query = query.filter(Transfer.dispatched_at <= date_to)

        total = query.count()
        transfers = (
            query.order_by(Transfer.dispatched_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        items = [
            TransferListItem(
                id=t.id,
                qr_number=t.qr_number,
                item_code=t.item_code,
                item_name=t.item_name,
                uom=t.uom,
                quantity_sent=t.quantity_sent,
                quantity_received=t.quantity_received,
                status=t.status,
                dispatched_at=t.dispatched_at,
                processed_at=t.processed_at,
            )
            for t in transfers
        ]
        return total, items

    def _resolve_scrapeyard_plant(
        self, db: Session, shopfloor_plant: Plant
    ) -> Optional[int]:
        if shopfloor_plant.linked_scrapeyard_plant_id:
            return shopfloor_plant.linked_scrapeyard_plant_id
        sy_plant = (
            db.query(Plant)
            .filter(
                Plant.app_role == AppRole.SCRAPEYARD,
                Plant.is_active.is_(True),
            )
            .first()
        )
        return sy_plant.id if sy_plant else None

    def dispatch(
        self,
        db: Session,
        plant_id: int,
        data: DispatchRequest,
    ) -> TransferResponse:
        employee = validate_employee(db, plant_id, data.employee_id)
        payload = parse_qr_payload(data.qr_raw)

        existing = (
            db.query(Transfer).filter(Transfer.qr_number == payload.qr_number).first()
        )
        if existing and existing.status != TransferStatus.PENDING:
            raise HTTPException(
                status_code=409,
                detail=f"QR already used with status {existing.status.value}",
            )

        shopfloor_plant = db.query(Plant).filter(Plant.id == plant_id).first()
        if not shopfloor_plant:
            raise HTTPException(status_code=404, detail="Plant not found")

        now = int(time.time())
        scrapeyard_id = self._resolve_scrapeyard_plant(db, shopfloor_plant)

        if existing:
            transfer = existing
            transfer.gp_number = data.gp_number
            transfer.status = TransferStatus.DISPATCHED
            transfer.dispatched_by = employee.id
            transfer.dispatched_at = now
            transfer.scrapeyard_plant_id = scrapeyard_id
        else:
            transfer = Transfer(
                qr_raw=data.qr_raw,
                qr_number=payload.qr_number,
                shopfloor_plant_id=plant_id,
                scrapeyard_plant_id=scrapeyard_id,
                item_code=payload.item_code,
                item_name=payload.item_name,
                description=payload.description,
                uom=payload.uom,
                quantity_sent=payload.quantity,
                gp_number=data.gp_number,
                location=payload.location,
                net_weight=payload.net_weight,
                tare_weight=payload.tare_weight,
                gross_weight=payload.gross_weight,
                status=TransferStatus.DISPATCHED,
                dispatched_by=employee.id,
                dispatched_at=now,
            )
            db.add(transfer)
            db.flush()

        db.add(
            TransferEvent(
                transfer_id=transfer.id,
                event_type=TransferEventType.DISPATCHED,
                actor_role=ActorRole.SHOPFLOOR,
                employee_profile_id=employee.id,
                employee_name=employee.name,
                quantity=transfer.quantity_sent,
                photo_path=data.photo_path,
                created_at=now,
            )
        )
        db.commit()
        db.refresh(transfer)
        return self._build_response(db, transfer)

    def accept(
        self,
        db: Session,
        plant_id: int,
        data: AcceptRequest,
    ) -> TransferResponse:
        employee = validate_employee(db, plant_id, data.employee_id)
        transfer = db.query(Transfer).filter(Transfer.id == data.transfer_id).first()
        if not transfer:
            raise HTTPException(status_code=404, detail="Transfer not found")
        if transfer.status != TransferStatus.DISPATCHED:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot accept transfer in status {transfer.status.value}",
            )
        if transfer.scrapeyard_plant_id and transfer.scrapeyard_plant_id != plant_id:
            raise HTTPException(status_code=403, detail="Transfer not for this plant")

        now = int(time.time())
        transfer.status = TransferStatus.ACCEPTED
        transfer.quantity_received = transfer.quantity_sent
        transfer.gr_number = data.gr_number
        transfer.processed_by = employee.id
        transfer.processed_at = now
        if not transfer.scrapeyard_plant_id:
            transfer.scrapeyard_plant_id = plant_id

        db.add(
            TransferEvent(
                transfer_id=transfer.id,
                event_type=TransferEventType.ACCEPTED,
                actor_role=ActorRole.SCRAPEYARD,
                employee_profile_id=employee.id,
                employee_name=employee.name,
                quantity=transfer.quantity_received,
                photo_path=data.photo_path,
                created_at=now,
            )
        )
        db.commit()
        db.refresh(transfer)
        return self._build_response(db, transfer)

    def reject(
        self,
        db: Session,
        plant_id: int,
        data: RejectRequest,
    ) -> TransferResponse:
        employee = validate_employee(db, plant_id, data.employee_id)
        transfer = db.query(Transfer).filter(Transfer.id == data.transfer_id).first()
        if not transfer:
            raise HTTPException(status_code=404, detail="Transfer not found")
        if transfer.status != TransferStatus.DISPATCHED:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot reject transfer in status {transfer.status.value}",
            )

        if data.reason_type == RejectionReasonType.QUANTITY_MISMATCH:
            if data.qty_received is None:
                raise HTTPException(
                    status_code=422, detail="qty_received required for quantity mismatch"
                )
            qty_received = data.qty_received
            comment = f"Received only {qty_received} {transfer.uom} of {transfer.item_name}"
        elif data.reason_type == RejectionReasonType.WRONG_MATERIAL:
            if not data.material_received_name:
                raise HTTPException(
                    status_code=422,
                    detail="material_received_name required for wrong material",
                )
            qty_received = Decimal("0")
            comment = (
                f"Received '{data.material_received_name}' instead of "
                f"'{transfer.item_name}'"
            )
        else:
            if not data.comment:
                raise HTTPException(
                    status_code=422, detail="comment required for others reason"
                )
            qty_received = Decimal("0")
            comment = data.comment

        now = int(time.time())
        transfer.status = TransferStatus.REJECTED
        transfer.quantity_received = qty_received
        transfer.processed_by = employee.id
        transfer.processed_at = now
        if not transfer.scrapeyard_plant_id:
            transfer.scrapeyard_plant_id = plant_id

        db.add(
            RejectionDetail(
                transfer_id=transfer.id,
                reason_type=data.reason_type,
                qty_received=qty_received,
                material_received_name=data.material_received_name,
                comment=data.comment or comment,
            )
        )
        db.add(
            TransferEvent(
                transfer_id=transfer.id,
                event_type=TransferEventType.REJECTED,
                actor_role=ActorRole.SCRAPEYARD,
                employee_profile_id=employee.id,
                employee_name=employee.name,
                quantity=qty_received,
                comment=comment,
                photo_path=data.photo_path,
                created_at=now,
            )
        )
        db.commit()
        db.refresh(transfer)
        return self._build_response(db, transfer)

    def acknowledge(
        self,
        db: Session,
        plant_id: int,
        transfer_id: int,
        employee_id: int,
    ) -> TransferResponse:
        employee = validate_employee(db, plant_id, employee_id)
        transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
        if not transfer:
            raise HTTPException(status_code=404, detail="Transfer not found")
        if transfer.shopfloor_plant_id != plant_id:
            raise HTTPException(status_code=403, detail="Transfer not for this plant")
        if transfer.status != TransferStatus.REJECTED:
            raise HTTPException(
                status_code=400,
                detail="Only rejected transfers can be acknowledged",
            )

        now = int(time.time())
        transfer.status = TransferStatus.ACKNOWLEDGED
        transfer.acknowledged_by = employee.id
        transfer.acknowledged_at = now

        db.add(
            TransferEvent(
                transfer_id=transfer.id,
                event_type=TransferEventType.ACKNOWLEDGED,
                actor_role=ActorRole.SHOPFLOOR,
                employee_profile_id=employee.id,
                employee_name=employee.name,
                quantity=transfer.quantity_received,
                created_at=now,
            )
        )
        db.commit()
        db.refresh(transfer)
        return self._build_response(db, transfer)


transfer_service = TransferService()
