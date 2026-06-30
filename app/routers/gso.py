from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_roles
from app.database.connection import get_db
from app.schemas.transfer import (
    GsoApproveRequest,
    GsoRejectRequest,
    TransferListResponse,
    TransferResponse,
)
from app.services.transfer import transfer_service

router = APIRouter(prefix="/v1/gso", tags=["gso"])

VALID_GSO_HISTORY_STATUSES = {"approved", "rejected", "auto_approved"}


def _parse_date(date_str: Optional[str]) -> Optional[int]:
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return int(dt.timestamp())
    except ValueError:
        return None


@router.get("/pending", response_model=TransferListResponse)
def list_pending(
    request: Request,
    item_code: Optional[str] = None,
    material_name: Optional[str] = None,
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _: bool = Depends(require_roles(["gso"])),
    db: Session = Depends(get_db),
):
    """List transfers awaiting GSO approval for the logged-in plant."""
    user = get_current_user(request)
    transfer_service.auto_approve_expired_gso(db)
    date_to_ts = _parse_date(date_to)
    if date_to_ts:
        date_to_ts += 86399
    total, items = transfer_service.list_transfers(
        db,
        gso_plant_id=user.get("plant_id"),
        item_code=item_code,
        material_name=material_name,
        date_from=_parse_date(date_from),
        date_to=date_to_ts,
        gso_pending_only=True,
        display_context="gso",
        skip=(page - 1) * page_size,
        limit=page_size,
    )
    return TransferListResponse(total=total, items=items)


@router.get("/history", response_model=TransferListResponse)
def list_history(
    request: Request,
    item_code: Optional[str] = None,
    material_name: Optional[str] = None,
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
    status: Optional[str] = Query(
        None,
        description="approved | rejected | auto_approved",
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _: bool = Depends(require_roles(["gso"])),
    db: Session = Depends(get_db),
):
    """List past GSO approval decisions for the logged-in plant."""
    if status is not None and status not in VALID_GSO_HISTORY_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status. Must be one of: {', '.join(sorted(VALID_GSO_HISTORY_STATUSES))}",
        )
    user = get_current_user(request)
    date_to_ts = _parse_date(date_to)
    if date_to_ts:
        date_to_ts += 86399
    total, items = transfer_service.list_transfers(
        db,
        gso_plant_id=user.get("plant_id"),
        item_code=item_code,
        material_name=material_name,
        date_from=_parse_date(date_from),
        date_to=date_to_ts,
        gso_history_only=status is None,
        gso_history_status=status,
        display_context="gso",
        skip=(page - 1) * page_size,
        limit=page_size,
    )
    return TransferListResponse(total=total, items=items)


@router.get("/{transfer_id}", response_model=TransferResponse)
def get_transfer(
    transfer_id: int,
    _: bool = Depends(require_roles(["gso"])),
    db: Session = Depends(get_db),
):
    """Get transfer detail with timeline."""
    return transfer_service.get_transfer(db, transfer_id)


@router.post("/approve", response_model=TransferResponse)
def approve_dispatch(
    body: GsoApproveRequest,
    request: Request,
    _: bool = Depends(require_roles(["gso"])),
    db: Session = Depends(get_db),
):
    """Approve a pending dispatch."""
    user = get_current_user(request)
    return transfer_service.approve_gso(
        db, user["gso_id"], user.get("plant_id"), body
    )


@router.post("/reject", response_model=TransferResponse)
def reject_dispatch(
    body: GsoRejectRequest,
    request: Request,
    _: bool = Depends(require_roles(["gso"])),
    db: Session = Depends(get_db),
):
    """Reject a pending dispatch with reason."""
    user = get_current_user(request)
    return transfer_service.reject_gso(
        db, user["gso_id"], user.get("plant_id"), body
    )
