from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.database.connection import get_db
from app.schemas.gso import GsoResponse, GsoUpdate
from app.services.gso_admin import gso_admin_service

router = APIRouter(prefix="/v1/plants", tags=["gso-admin"])


@router.get("/{plant_id}/gso", response_model=GsoResponse)
def get_gso_config(
    plant_id: int,
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    """Get GSO login and employees for a plant."""
    return gso_admin_service.get_config(db, plant_id)


@router.patch("/{plant_id}/gso", response_model=GsoResponse)
def update_gso_config(
    plant_id: int,
    body: GsoUpdate,
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    """Update GSO login, password, or employees for a plant."""
    return gso_admin_service.update_config(db, plant_id, body)
