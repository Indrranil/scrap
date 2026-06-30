from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_roles
from app.database.connection import get_db
from app.schemas.shred import (
    ReadyForSaleListResponse,
    ShredLogListResponse,
    ShredLogResponse,
    ShredQueueListResponse,
    ShredSaveRequest,
)
from app.schemas.transfer import AcceptRequest, RejectRequest, TransferResponse
from app.services.inventory import inventory_service
from app.services.shred import shred_service
from app.services.transfer import transfer_service

router = APIRouter(prefix="/v1/scrapeyard", tags=["scrapeyard"])


@router.post("/accept", response_model=TransferResponse)
def accept_material(
    body: AcceptRequest,
    user: dict = Depends(get_current_user),
    _: bool = Depends(require_roles(["scrapeyard"])),
    db: Session = Depends(get_db),
):
    """Accept a dispatched transfer."""
    return transfer_service.accept(db, user["scrapeyard_id"], body)


@router.post("/reject", response_model=TransferResponse)
def reject_material(
    body: RejectRequest,
    user: dict = Depends(get_current_user),
    _: bool = Depends(require_roles(["scrapeyard"])),
    db: Session = Depends(get_db),
):
    """Reject a dispatched transfer with reason."""
    return transfer_service.reject(db, user["scrapeyard_id"], body)


@router.get("/ready-for-sale", response_model=ReadyForSaleListResponse)
def list_ready_for_sale(
    user: dict = Depends(get_current_user),
    item_code: Optional[str] = None,
    material_name: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _: bool = Depends(require_roles(["scrapeyard"])),
    db: Session = Depends(get_db),
):
    """List non-p-item inventory ready for sale."""
    total, items = inventory_service.get_available(
        db,
        user["scrapeyard_id"],
        item_code=item_code,
        material_name=material_name,
        skip=(page - 1) * page_size,
        limit=page_size,
    )
    return ReadyForSaleListResponse(total=total, items=items)


@router.get("/shred-queue", response_model=ShredQueueListResponse)
def list_shred_queue(
    user: dict = Depends(get_current_user),
    item_code: Optional[str] = None,
    material_name: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _: bool = Depends(require_roles(["scrapeyard"])),
    db: Session = Depends(get_db),
):
    """List accepted P-items awaiting shred."""
    total, items = shred_service.list_shred_queue(
        db,
        user["scrapeyard_id"],
        item_code=item_code,
        material_name=material_name,
        skip=(page - 1) * page_size,
        limit=page_size,
    )
    return ShredQueueListResponse(total=total, items=items)


@router.post("/shred", response_model=ShredLogResponse, status_code=201)
def save_shred(
    body: ShredSaveRequest,
    user: dict = Depends(get_current_user),
    _: bool = Depends(require_roles(["scrapeyard"])),
    db: Session = Depends(get_db),
):
    """Record shred completion for an accepted P-item transfer."""
    return shred_service.save_shred(db, user["scrapeyard_id"], body)


@router.get("/shred-log", response_model=ShredLogListResponse)
def list_shred_log(
    user: dict = Depends(get_current_user),
    item_code: Optional[str] = None,
    material_name: Optional[str] = None,
    date_from: Optional[int] = None,
    date_to: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _: bool = Depends(require_roles(["scrapeyard"])),
    db: Session = Depends(get_db),
):
    """List shred log entries for the logged-in scrapeyard."""
    total, items = shred_service.list_shred_logs(
        db,
        scrapeyard_id=user["scrapeyard_id"],
        item_code=item_code,
        material_name=material_name,
        date_from=date_from,
        date_to=date_to,
        skip=(page - 1) * page_size,
        limit=page_size,
    )
    return ShredLogListResponse(total=total, items=items)


@router.get("/shred-log/{log_id}", response_model=ShredLogResponse)
def get_shred_log(
    log_id: int,
    _: bool = Depends(require_roles(["scrapeyard"])),
    db: Session = Depends(get_db),
):
    """Get a single shred log entry."""
    return shred_service.get_shred_log(db, log_id)
