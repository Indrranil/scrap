import time
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.auth.jwt_auth import hash_password
from app.models.employee_profile import EmployeeProfile
from app.models.security import Security
from app.schemas.auth import EmployeeSummary
from app.schemas.security_config import SecurityConfigResponse, SecurityConfigUpdate
from app.services.login_ids import assert_login_id_available


class SecurityAdminService:
    def get_active(self, db: Session) -> Security:
        security = (
            db.query(Security).filter(Security.is_active.is_(True)).first()
        )
        if not security:
            raise HTTPException(status_code=500, detail="Security not configured")
        return security

    def _to_response(
        self,
        db: Session,
        security: Security,
        *,
        generated_password: Optional[str] = None,
    ) -> SecurityConfigResponse:
        employees = (
            db.query(EmployeeProfile)
            .filter(
                EmployeeProfile.security_id == security.id,
                EmployeeProfile.is_active.is_(True),
            )
            .all()
        )
        return SecurityConfigResponse(
            id=security.id,
            name=security.name,
            login_id=security.login_id,
            is_active=security.is_active,
            employees=[EmployeeSummary(id=e.id, name=e.name) for e in employees],
            generated_password=generated_password,
        )

    def get_config(self, db: Session) -> SecurityConfigResponse:
        return self._to_response(db, self.get_active(db))

    def update_config(
        self, db: Session, data: SecurityConfigUpdate
    ) -> SecurityConfigResponse:
        security = self.get_active(db)
        generated_password: Optional[str] = None

        if data.login_id and data.login_id != security.login_id:
            assert_login_id_available(
                db, data.login_id, exclude_security_id=security.id
            )
            security.login_id = data.login_id

        if data.name is not None:
            security.name = data.name
        if data.password:
            generated_password = data.password
            security.password_hash = hash_password(data.password)

        if data.employee_names is not None:
            self._sync_employees(db, security.id, data.employee_names)

        db.commit()
        db.refresh(security)
        return self._to_response(db, security, generated_password=generated_password)

    def _sync_employees(
        self, db: Session, security_id: int, names: List[str]
    ) -> None:
        db.query(EmployeeProfile).filter(
            EmployeeProfile.security_id == security_id
        ).update({"is_active": False})
        for name in names:
            db.add(
                EmployeeProfile(
                    security_id=security_id,
                    name=name,
                    is_active=True,
                    created_at=int(time.time()),
                )
            )


security_admin_service = SecurityAdminService()
