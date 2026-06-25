from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_roles
from app.database.connection import get_db
from app.schemas.transfer import AcceptRequest, RejectRequest, TransferResponse
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
