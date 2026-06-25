from typing import List, Optional

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.employee_profile import EmployeeProfile


def require_roles(allowed_roles: List[str]):
    def role_checker(request: Request):
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return True

    return role_checker


def get_current_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def get_employee_id(
    x_employee_id: Optional[int] = Header(None, alias="X-Employee-Id"),
) -> Optional[int]:
    return x_employee_id


def validate_employee(
    db: Session,
    plant_id: int,
    employee_id: int,
) -> EmployeeProfile:
    employee = (
        db.query(EmployeeProfile)
        .filter(
            EmployeeProfile.id == employee_id,
            EmployeeProfile.plant_id == plant_id,
            EmployeeProfile.is_active.is_(True),
        )
        .first()
    )
    if not employee:
        raise HTTPException(status_code=400, detail="Invalid employee for this plant")
    return employee


def require_employee(
    request: Request,
    db: Session = Depends(get_db),
    x_employee_id: Optional[int] = Header(None, alias="X-Employee-Id"),
) -> EmployeeProfile:
    if x_employee_id is None:
        raise HTTPException(status_code=400, detail="X-Employee-Id header is required")
    user = get_current_user(request)
    plant_id = user.get("plant_id")
    if plant_id is None:
        raise HTTPException(status_code=400, detail="Plant context required")
    return validate_employee(db, plant_id, x_employee_id)
