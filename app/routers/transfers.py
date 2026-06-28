from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_roles
from app.database.connection import get_db
from app.models.enums import MaterialState, TransferStatus
from app.schemas.transfer import (
    QRScanRequest,
    QRScanResponse,
    TransferListResponse,
    TransferResponse,
)
from app.services.transfer import transfer_service

router = APIRouter(prefix="/v1/transfers", tags=["transfers"])


def _parse_date(date_str: Optional[str]) -> Optional[int]:
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return int(dt.timestamp())
    except ValueError:
        return None


@router.post("/scan", response_model=QRScanResponse)
def scan_qr(
    body: QRScanRequest,
    request: Request,
    _: bool = Depends(require_roles(["shopfloor", "scrapeyard"])),
    db: Session = Depends(get_db),
):
    """Parse QR payload and return material preview."""
    user = get_current_user(request)
    plant_id = user.get("plant_id") if user.get("role") == "shopfloor" else None
    return transfer_service.scan_qr(db, body.qr_raw, logged_in_plant_id=plant_id)


@router.get("/history", response_model=TransferListResponse)
def transfer_history(
    request: Request,
    item_code: Optional[str] = None,
    material_name: Optional[str] = None,
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
    status: Optional[TransferStatus] = None,
    material_state: Optional[MaterialState] = None,
    plant_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _: bool = Depends(require_roles(["shopfloor", "scrapeyard", "gso", "admin"])),
    db: Session = Depends(get_db),
):
    """List transfers with filters."""
    user = get_current_user(request)
    role = user.get("role")

    shopfloor_plant_id = None
    scrapeyard_id = None
    if role == "shopfloor":
        shopfloor_plant_id = user.get("plant_id")
    elif role == "scrapeyard":
        scrapeyard_id = user.get("scrapeyard_id")
    elif role == "admin" and plant_id:
        shopfloor_plant_id = plant_id

    date_to_ts = _parse_date(date_to)
    if date_to_ts:
        date_to_ts += 86399

    total, items = transfer_service.list_transfers(
        db,
        shopfloor_plant_id=shopfloor_plant_id,
        scrapeyard_id=scrapeyard_id,
        item_code=item_code,
        material_name=material_name,
        status=status,
        material_state=material_state,
        date_from=_parse_date(date_from),
        date_to=date_to_ts,
        skip=(page - 1) * page_size,
        limit=page_size,
    )
    return TransferListResponse(total=total, items=items)


@router.get("/{transfer_id}", response_model=TransferResponse)
def get_transfer(
    transfer_id: int,
    _: bool = Depends(require_roles(["shopfloor", "scrapeyard", "gso", "admin"])),
    db: Session = Depends(get_db),
):
    """Get transfer detail with timeline."""
    return transfer_service.get_transfer(db, transfer_id)
