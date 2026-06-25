from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.database.connection import get_db
from app.schemas.scrapeyard import ScrapeyardResponse, ScrapeyardUpdate
from app.services.scrapeyard import scrapeyard_service

router = APIRouter(prefix="/v1/scrapeyard-config", tags=["scrapeyard-admin"])


@router.get("", response_model=ScrapeyardResponse)
def get_scrapeyard_config(
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    """Get the shared scrapeyard configuration and employees."""
    return scrapeyard_service.get_config(db)


@router.patch("", response_model=ScrapeyardResponse)
def update_scrapeyard_config(
    body: ScrapeyardUpdate,
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    """Update scrapeyard login, password, or employees."""
    return scrapeyard_service.update_config(db, body)
