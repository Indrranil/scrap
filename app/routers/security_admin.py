from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.database.connection import get_db
from app.schemas.security_config import SecurityConfigResponse, SecurityConfigUpdate
from app.services.security_admin import security_admin_service

router = APIRouter(prefix="/v1/security-config", tags=["security-admin"])


@router.get("", response_model=SecurityConfigResponse)
def get_security_config(
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    """Get the shared security account configuration and employees."""
    return security_admin_service.get_config(db)


@router.patch("", response_model=SecurityConfigResponse)
def update_security_config(
    body: SecurityConfigUpdate,
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    """Update security login, password, or employees."""
    return security_admin_service.update_config(db, body)
