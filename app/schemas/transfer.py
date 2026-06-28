from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.enums import (
    DispatchMethod,
    MaterialState,
    RejectionReasonType,
    TransferEventType,
    TransferStatus,
)


class QRPayload(BaseModel):
    qr_number: str
    item_code: str
    item_name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[int] = None
    net_weight: Optional[Decimal] = None
    tare_weight: Optional[Decimal] = None
    gross_weight: Optional[Decimal] = None
    uom: str
    quantity: Decimal
    date_str: Optional[str] = None
    time_str: Optional[str] = None
    plu_code: Optional[str] = None
    item_code_8: Optional[str] = None
    is_p_item: bool = False
    is_shreddable: bool = False
    requires_material_state: bool = False


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
    employee_id: int
    material_state: Optional[MaterialState] = None


class ManualDispatchRequest(BaseModel):
    item_master_id: int
    quantity: Decimal = Field(..., gt=0)
    material_state: MaterialState
    employee_id: int


class AcceptRequest(BaseModel):
    transfer_id: int
    employee_id: int


class RejectRequest(BaseModel):
    transfer_id: int
    reason_type: RejectionReasonType
    employee_id: int
    qty_received: Optional[Decimal] = None
    material_received_name: Optional[str] = None
    comment: Optional[str] = None


class GsoApproveRequest(BaseModel):
    transfer_id: int
    employee_id: int


class GsoRejectRequest(BaseModel):
    transfer_id: int
    employee_id: int
    reason: str = Field(..., min_length=1)


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
    plu_code: Optional[str] = None
    item_code: str
    item_name: str
    description: Optional[str] = None
    uom: str
    quantity_sent: Decimal
    quantity_received: Optional[Decimal] = None
    location: Optional[int] = None
    net_weight: Optional[Decimal] = None
    tare_weight: Optional[Decimal] = None
    gross_weight: Optional[Decimal] = None
    dispatch_method: DispatchMethod
    material_state: MaterialState
    is_p_item: bool = False
    is_shreddable: bool = False
    status: TransferStatus
    dispatched_at: Optional[int] = None
    processed_at: Optional[int] = None
    acknowledged_at: Optional[int] = None
    gso_approved_at: Optional[int] = None
    gso_auto_approved: bool = False
    gso_rejected_at: Optional[int] = None
    gso_rejection_reason: Optional[str] = None
    events: List[TransferEventResponse] = []
    rejection: Optional[RejectionDetailResponse] = None

    class Config:
        from_attributes = True


class TransferListItem(BaseModel):
    id: int
    qr_number: str
    plu_code: Optional[str] = None
    item_code: str
    item_name: str
    uom: str
    quantity_sent: Decimal
    quantity_received: Optional[Decimal] = None
    dispatch_method: DispatchMethod
    material_state: MaterialState
    is_p_item: bool = False
    is_shreddable: bool = False
    status: TransferStatus
    dispatched_at: Optional[int] = None
    processed_at: Optional[int] = None
    gso_approved_at: Optional[int] = None
    gso_auto_approved: bool = False
    gso_rejected_at: Optional[int] = None

    class Config:
        from_attributes = True


class TransferListResponse(BaseModel):
    total: int
    items: List[TransferListItem]
