import time
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.auth.jwt_auth import create_access_token, hash_password, verify_password
from app.models.admin_user import AdminUser
from app.models.employee_profile import EmployeeProfile
from app.models.enums import AppRole
from app.models.plant import Plant
from app.schemas.auth import EmployeeSummary, LoginRequest, LoginResponse


class AuthService:
    def login(self, db: Session, request: LoginRequest) -> LoginResponse:
        admin = (
            db.query(AdminUser)
            .filter(
                AdminUser.username == request.login_id,
                AdminUser.is_active.is_(True),
            )
            .first()
        )
        if admin and verify_password(request.password, admin.password_hash):
            token = create_access_token(subject=f"admin:{admin.id}", role="admin")
            return LoginResponse(
                access_token=token,
                role="admin",
                admin_name=admin.name,
            )

        query = db.query(Plant).filter(
            Plant.login_id == request.login_id,
            Plant.is_active.is_(True),
        )
        if request.app_role:
            query = query.filter(Plant.app_role == request.app_role)
        plant = query.first()

        if not plant or not verify_password(request.password, plant.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        employees = (
            db.query(EmployeeProfile)
            .filter(
                EmployeeProfile.plant_id == plant.id,
                EmployeeProfile.is_active.is_(True),
            )
            .all()
        )

        token = create_access_token(
            subject=f"plant:{plant.id}",
            role=plant.app_role.value,
            plant_id=plant.id,
        )
        return LoginResponse(
            access_token=token,
            role=plant.app_role.value,
            plant_id=plant.id,
            plant_name=plant.name,
            employees=[EmployeeSummary(id=e.id, name=e.name) for e in employees],
        )

    def create_admin(
        self,
        db: Session,
        username: str,
        password: str,
        name: str,
    ) -> AdminUser:
        existing = db.query(AdminUser).filter(AdminUser.username == username).first()
        if existing:
            raise HTTPException(status_code=409, detail="Admin username already exists")
        admin = AdminUser(
            username=username,
            password_hash=hash_password(password),
            name=name,
            is_active=True,
            created_at=int(time.time()),
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin


auth_service = AuthService()
