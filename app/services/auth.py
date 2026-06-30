import time
from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.auth.jwt_auth import create_access_token, hash_password, verify_password
from app.models.admin_user import AdminUser
from app.models.employee_profile import EmployeeProfile
from app.models.gso import Gso
from app.models.plant import Plant
from app.models.scrapeyard import Scrapeyard
from app.models.security import Security
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

        security = (
            db.query(Security)
            .filter(
                Security.login_id == request.login_id,
                Security.is_active.is_(True),
            )
            .first()
        )
        if security and verify_password(request.password, security.password_hash):
            employees = self._security_employees(db, security.id)
            token = create_access_token(
                subject=f"security:{security.id}",
                role="security",
                security_id=security.id,
            )
            return LoginResponse(
                access_token=token,
                role="security",
                security_id=security.id,
                security_name=security.name,
                employees=employees,
            )

        gso = (
            db.query(Gso)
            .filter(
                Gso.login_id == request.login_id,
                Gso.is_active.is_(True),
            )
            .first()
        )
        if gso and verify_password(request.password, gso.password_hash):
            employees = self._gso_employees(db, gso.id)
            plant_name = None
            if gso.plant_id:
                plant = db.query(Plant).filter(Plant.id == gso.plant_id).first()
                plant_name = plant.name if plant else None
            token = create_access_token(
                subject=f"gso:{gso.id}",
                role="gso",
                gso_id=gso.id,
                plant_id=gso.plant_id,
            )
            return LoginResponse(
                access_token=token,
                role="gso",
                gso_id=gso.id,
                gso_name=gso.name,
                plant_id=gso.plant_id,
                plant_name=plant_name,
                employees=employees,
            )

        scrapeyard = (
            db.query(Scrapeyard)
            .filter(
                Scrapeyard.login_id == request.login_id,
                Scrapeyard.is_active.is_(True),
            )
            .first()
        )
        if scrapeyard and verify_password(request.password, scrapeyard.password_hash):
            employees = self._scrapeyard_employees(db, scrapeyard.id)
            token = create_access_token(
                subject=f"scrapeyard:{scrapeyard.id}",
                role="scrapeyard",
                scrapeyard_id=scrapeyard.id,
            )
            return LoginResponse(
                access_token=token,
                role="scrapeyard",
                scrapeyard_id=scrapeyard.id,
                scrapeyard_name=scrapeyard.name,
                employees=employees,
            )

        plant = (
            db.query(Plant)
            .filter(
                Plant.login_id == request.login_id,
                Plant.is_active.is_(True),
            )
            .first()
        )
        if plant and verify_password(request.password, plant.password_hash):
            employees = self._plant_employees(db, plant.id)
            token = create_access_token(
                subject=f"plant:{plant.id}",
                role="shopfloor",
                plant_id=plant.id,
            )
            return LoginResponse(
                access_token=token,
                role="shopfloor",
                plant_id=plant.id,
                plant_name=plant.name,
                employees=employees,
            )

        raise HTTPException(status_code=401, detail="Invalid credentials")

    def _plant_employees(self, db: Session, plant_id: int) -> List[EmployeeSummary]:
        rows = (
            db.query(EmployeeProfile)
            .filter(
                EmployeeProfile.plant_id == plant_id,
                EmployeeProfile.is_active.is_(True),
            )
            .all()
        )
        return [EmployeeSummary(id=e.id, name=e.name) for e in rows]

    def _scrapeyard_employees(
        self, db: Session, scrapeyard_id: int
    ) -> List[EmployeeSummary]:
        rows = (
            db.query(EmployeeProfile)
            .filter(
                EmployeeProfile.scrapeyard_id == scrapeyard_id,
                EmployeeProfile.is_active.is_(True),
            )
            .all()
        )
        return [EmployeeSummary(id=e.id, name=e.name) for e in rows]

    def _gso_employees(self, db: Session, gso_id: int) -> List[EmployeeSummary]:
        rows = (
            db.query(EmployeeProfile)
            .filter(
                EmployeeProfile.gso_id == gso_id,
                EmployeeProfile.is_active.is_(True),
            )
            .all()
        )
        return [EmployeeSummary(id=e.id, name=e.name) for e in rows]

    def _security_employees(
        self, db: Session, security_id: int
    ) -> List[EmployeeSummary]:
        rows = (
            db.query(EmployeeProfile)
            .filter(
                EmployeeProfile.security_id == security_id,
                EmployeeProfile.is_active.is_(True),
            )
            .all()
        )
        return [EmployeeSummary(id=e.id, name=e.name) for e in rows]

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
