import hashlib
import time
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import validate_plant_employee, validate_scrapeyard_employee
from app.models.enums import (
    ActorRole,
    DispatchMethod,
    MaterialState,
    RejectionReasonType,
    TransferEventType,
    TransferStatus,
)
from app.models.item_master import ItemMaster
from app.models.rejection_detail import RejectionDetail
from app.models.transfer import Transfer
from app.models.transfer_event import TransferEvent
from app.schemas.transfer import (
    AcceptRequest,
    DispatchRequest,
    ManualDispatchRequest,
    QRScanResponse,
    RejectRequest,
    RejectionDetailResponse,
    ResolvedPlantInfo,
    TransferEventResponse,
    TransferListItem,
    TransferResponse,
)
from app.services.item_master import item_master_service
from app.services.plant_resolver import resolve_plant_by_qr_location
from app.services.qr_parser import parse_qr_payload
from app.services.scrapeyard import scrapeyard_service


class TransferService:
    def _resolve_material_state(
        self,
        item: ItemMaster,
        requested: Optional[MaterialState],
    ) -> MaterialState:
        if not item.is_shreddable:
            return MaterialState.NOT_SHREDDED
        if requested is None:
            raise HTTPException(
                status_code=422,
                detail="material_state is required for shreddable items",
            )
        return requested

    def _enrich_payload_from_item(self, db: Session, payload) -> None:
        item = item_master_service.get_by_plu_code(db, payload.plu_code or payload.item_code)
        if not item:
            raise HTTPException(
                status_code=422,
                detail=f"Unknown item code: {payload.plu_code or payload.item_code}",
            )
        if item.uom.upper() == "EA":
            raise HTTPException(
                status_code=422,
                detail="EA items must use manual dispatch",
            )
        payload.item_name = item.name
        payload.description = item.name
        payload.uom = item.uom.upper()
        payload.plu_code = item.plu_code
        payload.is_p_item = item.is_p_item
        payload.is_shreddable = item.is_shreddable
        payload.requires_material_state = item.is_shreddable
        if item.is_p_item:
            payload.item_code_8 = None
        else:
            payload.item_code_8 = item.item_code

    def _transfer_is_shreddable(self, db: Session, transfer: Transfer) -> bool:
        if transfer.item_master_id:
            item = (
                db.query(ItemMaster)
                .filter(ItemMaster.id == transfer.item_master_id)
                .first()
            )
            if item:
                return item.is_shreddable
        if transfer.plu_code:
            item = item_master_service.get_by_plu_code(db, transfer.plu_code)
            if item:
                return item.is_shreddable
        return False

    def scan_qr(
        self,
        db: Session,
        qr_raw: str,
        logged_in_plant_id: Optional[int] = None,
    ) -> QRScanResponse:
        payload = parse_qr_payload(qr_raw)
        self._enrich_payload_from_item(db, payload)

        existing = (
            db.query(Transfer).filter(Transfer.qr_number == payload.qr_number).first()
        )

        resolved_plant = None
        plant_match = None
        if payload.location is not None:
            plant = resolve_plant_by_qr_location(db, payload.location)
            resolved_plant = ResolvedPlantInfo(
                id=plant.id,
                code=plant.code,
                name=plant.name,
                login_id=plant.login_id,
                qr_location=plant.qr_location,
            )
            if logged_in_plant_id is not None:
                plant_match = plant.id == logged_in_plant_id

        return QRScanResponse(
            payload=payload,
            resolved_plant=resolved_plant,
            plant_match=plant_match,
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
            plu_code=transfer.plu_code,
            item_code=transfer.item_code,
            item_name=transfer.item_name,
            description=transfer.description,
            uom=transfer.uom,
            quantity_sent=transfer.quantity_sent,
            quantity_received=transfer.quantity_received,
            location=transfer.location,
            net_weight=transfer.net_weight,
            tare_weight=transfer.tare_weight,
            gross_weight=transfer.gross_weight,
            dispatch_method=transfer.dispatch_method,
            material_state=transfer.material_state,
            is_p_item=transfer.is_p_item,
            is_shreddable=self._transfer_is_shreddable(db, transfer),
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
        shopfloor_plant_id: Optional[int] = None,
        scrapeyard_id: Optional[int] = None,
        item_code: Optional[str] = None,
        material_name: Optional[str] = None,
        status: Optional[TransferStatus] = None,
        material_state: Optional[MaterialState] = None,
        date_from: Optional[int] = None,
        date_to: Optional[int] = None,
        rejected_only: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[int, List[TransferListItem]]:
        query = db.query(Transfer)

        if shopfloor_plant_id:
            query = query.filter(Transfer.shopfloor_plant_id == shopfloor_plant_id)
        if scrapeyard_id:
            query = query.filter(Transfer.scrapeyard_id == scrapeyard_id)

        if item_code:
            query = query.filter(
                (Transfer.item_code.ilike(f"%{item_code}%"))
                | (Transfer.plu_code.ilike(f"%{item_code}%"))
            )
        if material_name:
            query = query.filter(Transfer.item_name.ilike(f"%{material_name}%"))
        if status:
            query = query.filter(Transfer.status == status)
        if material_state:
            query = query.filter(Transfer.material_state == material_state)
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
                plu_code=t.plu_code,
                item_code=t.item_code,
                item_name=t.item_name,
                uom=t.uom,
                quantity_sent=t.quantity_sent,
                quantity_received=t.quantity_received,
                dispatch_method=t.dispatch_method,
                material_state=t.material_state,
                is_p_item=t.is_p_item,
                is_shreddable=self._transfer_is_shreddable(db, t),
                status=t.status,
                dispatched_at=t.dispatched_at,
                processed_at=t.processed_at,
            )
            for t in transfers
        ]
        return total, items

    def dispatch(
        self,
        db: Session,
        logged_in_plant_id: int,
        data: DispatchRequest,
    ) -> TransferResponse:
        employee = validate_plant_employee(db, logged_in_plant_id, data.employee_id)
        payload = parse_qr_payload(data.qr_raw)
        self._enrich_payload_from_item(db, payload)

        item = item_master_service.get_by_plu_code(
            db, payload.plu_code or payload.item_code
        )
        if not item:
            raise HTTPException(status_code=422, detail="Unknown item code")

        material_state = self._resolve_material_state(item, data.material_state)

        if payload.location is None:
            raise HTTPException(
                status_code=422, detail="QR payload must include LOCATION"
            )

        qr_plant = resolve_plant_by_qr_location(db, payload.location)
        if qr_plant.id != logged_in_plant_id:
            raise HTTPException(
                status_code=403,
                detail=(
                    f"QR belongs to {qr_plant.name} ({qr_plant.login_id}); "
                    f"you are logged in as a different plant"
                ),
            )

        existing = (
            db.query(Transfer).filter(Transfer.qr_number == payload.qr_number).first()
        )
        if existing and existing.status != TransferStatus.PENDING:
            raise HTTPException(
                status_code=409,
                detail=f"QR already used with status {existing.status.value}",
            )

        scrapeyard = scrapeyard_service.get_active(db)
        now = int(time.time())
        if item.is_p_item:
            stored_item_code = item.plu_code
        else:
            stored_item_code = item.item_code or item.plu_code

        if existing:
            transfer = existing
            transfer.status = TransferStatus.DISPATCHED
            transfer.dispatched_by = employee.id
            transfer.dispatched_at = now
            transfer.scrapeyard_id = scrapeyard.id
            transfer.shopfloor_plant_id = qr_plant.id
            transfer.item_master_id = item.id
            transfer.plu_code = item.plu_code
            transfer.item_code = stored_item_code
            transfer.item_name = item.name
            transfer.description = item.name
            transfer.uom = item.uom.upper()
            transfer.quantity_sent = payload.quantity
            transfer.material_state = material_state
            transfer.dispatch_method = DispatchMethod.QR
            transfer.is_p_item = item.is_p_item
        else:
            transfer = Transfer(
                qr_raw=data.qr_raw,
                qr_number=payload.qr_number,
                shopfloor_plant_id=qr_plant.id,
                scrapeyard_id=scrapeyard.id,
                item_master_id=item.id,
                plu_code=item.plu_code,
                item_code=stored_item_code,
                item_name=item.name,
                description=item.name,
                uom=item.uom.upper(),
                quantity_sent=payload.quantity,
                location=payload.location,
                net_weight=payload.net_weight,
                tare_weight=payload.tare_weight,
                gross_weight=payload.gross_weight,
                dispatch_method=DispatchMethod.QR,
                material_state=material_state,
                is_p_item=item.is_p_item,
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
                created_at=now,
            )
        )
        db.commit()
        db.refresh(transfer)
        return self._build_response(db, transfer)

    def dispatch_manual(
        self,
        db: Session,
        logged_in_plant_id: int,
        data: ManualDispatchRequest,
    ) -> TransferResponse:
        employee = validate_plant_employee(db, logged_in_plant_id, data.employee_id)
        item = item_master_service.get_by_id(db, data.item_master_id)

        if item.uom.upper() != "EA":
            raise HTTPException(
                status_code=422,
                detail="KG items must use QR dispatch",
            )

        material_state = self._resolve_material_state(item, data.material_state)
        scrapeyard = scrapeyard_service.get_active(db)
        now = int(time.time())
        canonical_item_code = item.item_code or item.plu_code
        qr_raw = (
            f"MANUAL DISPATCH\nPLU: {item.plu_code}\nNAME: {item.name}\n"
            f"QTY: {data.quantity}\nPLANT: {logged_in_plant_id}\nAT: {now}"
        )
        qr_number = hashlib.sha256(qr_raw.encode()).hexdigest()[:16]

        transfer = Transfer(
            qr_raw=qr_raw,
            qr_number=qr_number,
            shopfloor_plant_id=logged_in_plant_id,
            scrapeyard_id=scrapeyard.id,
            item_master_id=item.id,
            plu_code=item.plu_code,
            item_code=canonical_item_code,
            item_name=item.name,
            description=item.name,
            uom=item.uom.upper(),
            quantity_sent=data.quantity,
            dispatch_method=DispatchMethod.MANUAL,
            material_state=material_state,
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
                created_at=now,
            )
        )
        db.commit()
        db.refresh(transfer)
        return self._build_response(db, transfer)

    def accept(
        self,
        db: Session,
        scrapeyard_id: int,
        data: AcceptRequest,
    ) -> TransferResponse:
        employee = validate_scrapeyard_employee(
            db, scrapeyard_id, data.employee_id
        )
        transfer = db.query(Transfer).filter(Transfer.id == data.transfer_id).first()
        if not transfer:
            raise HTTPException(status_code=404, detail="Transfer not found")
        if transfer.status != TransferStatus.DISPATCHED:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot accept transfer in status {transfer.status.value}",
            )
        if transfer.scrapeyard_id and transfer.scrapeyard_id != scrapeyard_id:
            raise HTTPException(status_code=403, detail="Transfer not for this scrapeyard")

        now = int(time.time())
        transfer.status = TransferStatus.ACCEPTED
        transfer.quantity_received = transfer.quantity_sent
        transfer.processed_by = employee.id
        transfer.processed_at = now
        if not transfer.scrapeyard_id:
            transfer.scrapeyard_id = scrapeyard_id

        db.add(
            TransferEvent(
                transfer_id=transfer.id,
                event_type=TransferEventType.ACCEPTED,
                actor_role=ActorRole.SCRAPEYARD,
                employee_profile_id=employee.id,
                employee_name=employee.name,
                quantity=transfer.quantity_received,
                created_at=now,
            )
        )
        db.commit()
        db.refresh(transfer)
        return self._build_response(db, transfer)

    def reject(
        self,
        db: Session,
        scrapeyard_id: int,
        data: RejectRequest,
    ) -> TransferResponse:
        employee = validate_scrapeyard_employee(
            db, scrapeyard_id, data.employee_id
        )
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
        if not transfer.scrapeyard_id:
            transfer.scrapeyard_id = scrapeyard_id

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
        employee = validate_plant_employee(db, plant_id, employee_id)
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
