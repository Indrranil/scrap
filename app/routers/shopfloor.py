from typing import Optional

from fastapi import APIRouter, Depends, Header, Query, Request
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_roles
from app.database.connection import get_db
from app.schemas.transfer import DispatchRequest, TransferListResponse, TransferResponse
from app.services.transfer import transfer_service

router = APIRouter(prefix="/v1/shopfloor", tags=["shopfloor"])


@router.post("/dispatch", response_model=TransferResponse)
def dispatch_material(
    body: DispatchRequest,
    request: Request,
    _: bool = Depends(require_roles(["shopfloor"])),
    db: Session = Depends(get_db),
):
    """Confirm dispatch after QR scan. Logged-in plant must match QR location."""
    user = get_current_user(request)
    return transfer_service.dispatch(db, user["plant_id"], body)


@router.get("/rejected", response_model=TransferListResponse)
def list_rejected(
    request: Request,
    item_code: Optional[str] = None,
    material_name: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _: bool = Depends(require_roles(["shopfloor"])),
    db: Session = Depends(get_db),
):
    """List rejected transfers awaiting acknowledgement."""
    user = get_current_user(request)
    total, items = transfer_service.list_transfers(
        db,
        shopfloor_plant_id=user["plant_id"],
        item_code=item_code,
        material_name=material_name,
        rejected_only=True,
        skip=(page - 1) * page_size,
        limit=page_size,
    )
    return TransferListResponse(total=total, items=items)


@router.post("/rejected/{transfer_id}/acknowledge", response_model=TransferResponse)
def acknowledge_rejection(
    transfer_id: int,
    request: Request,
    employee_id: int = Header(..., alias="X-Employee-Id"),
    _: bool = Depends(require_roles(["shopfloor"])),
    db: Session = Depends(get_db),
):
    """Acknowledge a rejected dispatch."""
    user = get_current_user(request)
    return transfer_service.acknowledge(
        db, user["plant_id"], transfer_id, employee_id
    )
