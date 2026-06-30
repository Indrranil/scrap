from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_roles
from app.database.connection import get_db
from app.schemas.admin import AdminProfileResponse, AdminProfileUpdate
from app.services.auth import auth_service

router = APIRouter(prefix="/v1/admin", tags=["admin-profile"])


@router.get("/profile", response_model=AdminProfileResponse)
def get_profile(
    request: Request,
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    """Get the logged-in admin profile."""
    user = get_current_user(request)
    admin = auth_service.get_admin_profile(db, user)
    return AdminProfileResponse(username=admin.username, name=admin.name)


@router.patch("/profile", response_model=AdminProfileResponse)
def update_profile(
    body: AdminProfileUpdate,
    request: Request,
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    """Update admin display name or password."""
    user = get_current_user(request)
    admin = auth_service.update_admin_profile(db, user, body)
    return AdminProfileResponse(username=admin.username, name=admin.name)
