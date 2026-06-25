from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel

from app.models.enums import RejectionReasonType, TransferEventType, TransferStatus


class QRPayload(BaseModel):
    qr_number: str
    item_code: str
    item_name: str
    description: Optional[str] = None
    location: Optional[int] = None
    net_weight: Optional[Decimal] = None
    tare_weight: Optional[Decimal] = None
    gross_weight: Optional[Decimal] = None
    uom: str
    quantity: Decimal
    date_str: Optional[str] = None
    time_str: Optional[str] = None


class ResolvedPlantInfo(BaseModel):
    id: int
    code: Optional[str] = None
    name: str
    login_id: str
    qr_location: int


class QRScanRequest(BaseModel):
    qr_raw: str


class QRScanResponse(BaseModel):
    payload: QRPayload
    resolved_plant: Optional[ResolvedPlantInfo] = None
    plant_match: Optional[bool] = None
    existing_transfer_id: Optional[int] = None
    existing_status: Optional[TransferStatus] = None


class DispatchRequest(BaseModel):
    qr_raw: str
    gp_number: str
    employee_id: int


class AcceptRequest(BaseModel):
    transfer_id: int
    gr_number: str
    employee_id: int


class RejectRequest(BaseModel):
    transfer_id: int
    reason_type: RejectionReasonType
    employee_id: int
    qty_received: Optional[Decimal] = None
    material_received_name: Optional[str] = None
    comment: Optional[str] = None


class TransferEventResponse(BaseModel):
    id: int
    event_type: TransferEventType
    actor_role: str
    employee_name: str
    quantity: Optional[Decimal] = None
    comment: Optional[str] = None
    created_at: int

    class Config:
        from_attributes = True


class RejectionDetailResponse(BaseModel):
    reason_type: RejectionReasonType
    qty_received: Optional[Decimal] = None
    material_received_name: Optional[str] = None
    comment: Optional[str] = None

    class Config:
        from_attributes = True


class TransferResponse(BaseModel):
    id: int
    qr_number: str
    item_code: str
    item_name: str
    description: Optional[str] = None
    uom: str
    quantity_sent: Decimal
    quantity_received: Optional[Decimal] = None
    gp_number: Optional[str] = None
    gr_number: Optional[str] = None
    location: Optional[int] = None
    net_weight: Optional[Decimal] = None
    tare_weight: Optional[Decimal] = None
    gross_weight: Optional[Decimal] = None
    status: TransferStatus
    dispatched_at: Optional[int] = None
    processed_at: Optional[int] = None
    acknowledged_at: Optional[int] = None
    events: List[TransferEventResponse] = []
    rejection: Optional[RejectionDetailResponse] = None

    class Config:
        from_attributes = True


class TransferListItem(BaseModel):
    id: int
    qr_number: str
    item_code: str
    item_name: str
    uom: str
    quantity_sent: Decimal
    quantity_received: Optional[Decimal] = None
    status: TransferStatus
    dispatched_at: Optional[int] = None
    processed_at: Optional[int] = None

    class Config:
        from_attributes = True


class TransferListResponse(BaseModel):
    total: int
    items: List[TransferListItem]
