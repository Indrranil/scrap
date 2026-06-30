from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.admin_user import AdminUser
from app.models.gso import Gso
from app.models.plant import Plant
from app.models.scrapeyard import Scrapeyard
from app.models.security import Security


def assert_login_id_available(
    db: Session,
    login_id: str,
    *,
    exclude_plant_id: Optional[int] = None,
    exclude_gso_id: Optional[int] = None,
    exclude_security_id: Optional[int] = None,
    exclude_scrapeyard_id: Optional[int] = None,
) -> None:
    """Ensure login_id is unique across all login-bearing entities."""
    if (
        db.query(AdminUser)
        .filter(AdminUser.username == login_id, AdminUser.is_active.is_(True))
        .first()
    ):
        raise HTTPException(status_code=409, detail="Login ID already exists")

    plant_q = db.query(Plant).filter(Plant.login_id == login_id)
    if exclude_plant_id:
        plant_q = plant_q.filter(Plant.id != exclude_plant_id)
    if plant_q.first():
        raise HTTPException(status_code=409, detail="Login ID already exists")

    gso_q = db.query(Gso).filter(Gso.login_id == login_id)
    if exclude_gso_id:
        gso_q = gso_q.filter(Gso.id != exclude_gso_id)
    if gso_q.first():
        raise HTTPException(status_code=409, detail="Login ID already exists")

    sec_q = db.query(Security).filter(Security.login_id == login_id)
    if exclude_security_id:
        sec_q = sec_q.filter(Security.id != exclude_security_id)
    if sec_q.first():
        raise HTTPException(status_code=409, detail="Login ID already exists")

    sy_q = db.query(Scrapeyard).filter(Scrapeyard.login_id == login_id)
    if exclude_scrapeyard_id:
        sy_q = sy_q.filter(Scrapeyard.id != exclude_scrapeyard_id)
    if sy_q.first():
        raise HTTPException(status_code=409, detail="Login ID already exists")
