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


def validate_plant_employee(
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


def validate_scrapeyard_employee(
    db: Session,
    scrapeyard_id: int,
    employee_id: int,
) -> EmployeeProfile:
    employee = (
        db.query(EmployeeProfile)
        .filter(
            EmployeeProfile.id == employee_id,
            EmployeeProfile.scrapeyard_id == scrapeyard_id,
            EmployeeProfile.is_active.is_(True),
        )
        .first()
    )
    if not employee:
        raise HTTPException(
            status_code=400, detail="Invalid employee for this scrapeyard"
        )
    return employee


def validate_gso_employee(
    db: Session,
    gso_id: int,
    employee_id: int,
) -> EmployeeProfile:
    employee = (
        db.query(EmployeeProfile)
        .filter(
            EmployeeProfile.id == employee_id,
            EmployeeProfile.gso_id == gso_id,
            EmployeeProfile.is_active.is_(True),
        )
        .first()
    )
    if not employee:
        raise HTTPException(status_code=400, detail="Invalid employee for this GSO")
    return employee


def validate_security_employee(
    db: Session,
    security_id: int,
    employee_id: int,
) -> EmployeeProfile:
    employee = (
        db.query(EmployeeProfile)
        .filter(
            EmployeeProfile.id == employee_id,
            EmployeeProfile.security_id == security_id,
            EmployeeProfile.is_active.is_(True),
        )
        .first()
    )
    if not employee:
        raise HTTPException(
            status_code=400, detail="Invalid employee for this security account"
        )
    return employee
