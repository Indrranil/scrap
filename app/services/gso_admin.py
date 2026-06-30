import time
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.auth.jwt_auth import hash_password
from app.models.employee_profile import EmployeeProfile
from app.models.gso import Gso
from app.models.plant import Plant
from app.schemas.auth import EmployeeSummary
from app.schemas.gso import GsoResponse, GsoUpdate
from app.services.login_ids import assert_login_id_available

DEFAULT_GSO_PASSWORD = "1234"


class GsoAdminService:
    def _to_response(
        self,
        db: Session,
        gso: Gso,
        *,
        generated_password: Optional[str] = None,
    ) -> GsoResponse:
        employees = (
            db.query(EmployeeProfile)
            .filter(
                EmployeeProfile.gso_id == gso.id,
                EmployeeProfile.is_active.is_(True),
            )
            .all()
        )
        return GsoResponse(
            id=gso.id,
            plant_id=gso.plant_id,
            name=gso.name,
            login_id=gso.login_id,
            is_active=gso.is_active,
            employees=[EmployeeSummary(id=e.id, name=e.name) for e in employees],
            generated_password=generated_password,
        )

    def _get_plant(self, db: Session, plant_id: int) -> Plant:
        plant = (
            db.query(Plant)
            .filter(Plant.id == plant_id, Plant.is_active.is_(True))
            .first()
        )
        if not plant:
            raise HTTPException(status_code=404, detail="Plant not found")
        return plant

    def _get_gso_for_plant(self, db: Session, plant_id: int) -> Gso:
        gso = (
            db.query(Gso)
            .filter(Gso.plant_id == plant_id, Gso.is_active.is_(True))
            .first()
        )
        if not gso:
            raise HTTPException(status_code=404, detail="GSO not configured for plant")
        return gso

    def ensure_gso_for_plant(
        self,
        db: Session,
        plant: Plant,
        *,
        password: Optional[str] = None,
    ) -> Gso:
        login_id = f"GSO-{plant.login_id}"
        existing = (
            db.query(Gso)
            .filter((Gso.plant_id == plant.id) | (Gso.login_id == login_id))
            .first()
        )
        if existing:
            if not existing.plant_id:
                existing.plant_id = plant.id
            return existing

        plain_password = password or DEFAULT_GSO_PASSWORD
        gso = Gso(
            plant_id=plant.id,
            name=f"GSO {plant.name}",
            login_id=login_id,
            password_hash=hash_password(plain_password),
            is_active=True,
            created_at=int(time.time()),
        )
        db.add(gso)
        db.flush()
        return gso

    def get_config(self, db: Session, plant_id: int) -> GsoResponse:
        self._get_plant(db, plant_id)
        gso = self._get_gso_for_plant(db, plant_id)
        return self._to_response(db, gso)

    def update_config(
        self, db: Session, plant_id: int, data: GsoUpdate
    ) -> GsoResponse:
        self._get_plant(db, plant_id)
        gso = self._get_gso_for_plant(db, plant_id)
        generated_password: Optional[str] = None

        if data.login_id and data.login_id != gso.login_id:
            assert_login_id_available(
                db, data.login_id, exclude_gso_id=gso.id, exclude_plant_id=plant_id
            )
            gso.login_id = data.login_id

        if data.name is not None:
            gso.name = data.name
        if data.password:
            generated_password = data.password
            gso.password_hash = hash_password(data.password)

        if data.employee_names is not None:
            self._sync_employees(db, gso.id, data.employee_names)

        db.commit()
        db.refresh(gso)
        return self._to_response(db, gso, generated_password=generated_password)

    def _sync_employees(self, db: Session, gso_id: int, names: List[str]) -> None:
        db.query(EmployeeProfile).filter(EmployeeProfile.gso_id == gso_id).update(
            {"is_active": False}
        )
        for name in names:
            db.add(
                EmployeeProfile(
                    gso_id=gso_id,
                    name=name,
                    is_active=True,
                    created_at=int(time.time()),
                )
            )


gso_admin_service = GsoAdminService()
