import time
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.auth.jwt_auth import hash_password
from app.models.employee_profile import EmployeeProfile
from app.models.plant import Plant
from app.schemas.auth import EmployeeSummary
from app.schemas.plant import PlantCreate, PlantResponse, PlantUpdate


class PlantService:
    def _to_response(self, db: Session, plant: Plant) -> PlantResponse:
        employees = (
            db.query(EmployeeProfile)
            .filter(
                EmployeeProfile.plant_id == plant.id,
                EmployeeProfile.is_active.is_(True),
            )
            .all()
        )
        return PlantResponse(
            id=plant.id,
            code=plant.code,
            name=plant.name,
            login_id=plant.login_id,
            app_role=plant.app_role,
            address=plant.address,
            linked_scrapeyard_plant_id=plant.linked_scrapeyard_plant_id,
            is_active=plant.is_active,
            employees=[EmployeeSummary(id=e.id, name=e.name) for e in employees],
        )

    def list_plants(
        self, db: Session, search: Optional[str] = None
    ) -> List[PlantResponse]:
        query = db.query(Plant).filter(Plant.is_active.is_(True))
        if search:
            like = f"%{search}%"
            query = query.filter(
                (Plant.name.ilike(like))
                | (Plant.code.ilike(like))
                | (Plant.login_id.ilike(like))
            )
        plants = query.order_by(Plant.id.desc()).all()
        return [self._to_response(db, p) for p in plants]

    def get_plant(self, db: Session, plant_id: int) -> PlantResponse:
        plant = (
            db.query(Plant)
            .filter(Plant.id == plant_id, Plant.is_active.is_(True))
            .first()
        )
        if not plant:
            raise HTTPException(status_code=404, detail="Plant not found")
        return self._to_response(db, plant)

    def create_plant(self, db: Session, data: PlantCreate) -> PlantResponse:
        existing = db.query(Plant).filter(Plant.login_id == data.login_id).first()
        if existing:
            raise HTTPException(status_code=409, detail="Login ID already exists")

        plant = Plant(
            code=data.code,
            name=data.name,
            login_id=data.login_id,
            password_hash=hash_password(data.password),
            app_role=data.app_role,
            address=data.address,
            linked_scrapeyard_plant_id=data.linked_scrapeyard_plant_id,
            is_active=True,
            created_at=int(time.time()),
        )
        db.add(plant)
        db.flush()

        for name in data.employee_names:
            db.add(
                EmployeeProfile(
                    plant_id=plant.id,
                    name=name,
                    is_active=True,
                    created_at=int(time.time()),
                )
            )
        db.commit()
        db.refresh(plant)
        return self._to_response(db, plant)

    def update_plant(
        self, db: Session, plant_id: int, data: PlantUpdate
    ) -> PlantResponse:
        plant = (
            db.query(Plant)
            .filter(Plant.id == plant_id, Plant.is_active.is_(True))
            .first()
        )
        if not plant:
            raise HTTPException(status_code=404, detail="Plant not found")

        if data.login_id and data.login_id != plant.login_id:
            conflict = (
                db.query(Plant)
                .filter(Plant.login_id == data.login_id, Plant.id != plant_id)
                .first()
            )
            if conflict:
                raise HTTPException(status_code=409, detail="Login ID already exists")
            plant.login_id = data.login_id

        if data.code is not None:
            plant.code = data.code
        if data.name is not None:
            plant.name = data.name
        if data.password:
            plant.password_hash = hash_password(data.password)
        if data.app_role is not None:
            plant.app_role = data.app_role
        if data.address is not None:
            plant.address = data.address
        if data.linked_scrapeyard_plant_id is not None:
            plant.linked_scrapeyard_plant_id = data.linked_scrapeyard_plant_id

        if data.employee_names is not None:
            db.query(EmployeeProfile).filter(
                EmployeeProfile.plant_id == plant.id
            ).update({"is_active": False})
            for name in data.employee_names:
                db.add(
                    EmployeeProfile(
                        plant_id=plant.id,
                        name=name,
                        is_active=True,
                        created_at=int(time.time()),
                    )
                )

        db.commit()
        db.refresh(plant)
        return self._to_response(db, plant)

    def delete_plant(self, db: Session, plant_id: int) -> PlantResponse:
        plant = (
            db.query(Plant)
            .filter(Plant.id == plant_id, Plant.is_active.is_(True))
            .first()
        )
        if not plant:
            raise HTTPException(status_code=404, detail="Plant not found")
        plant.is_active = False
        db.commit()
        return self._to_response(db, plant)

    def copy_plant(self, db: Session, plant_id: int) -> PlantResponse:
        source = (
            db.query(Plant)
            .filter(Plant.id == plant_id, Plant.is_active.is_(True))
            .first()
        )
        if not source:
            raise HTTPException(status_code=404, detail="Plant not found")

        employees = (
            db.query(EmployeeProfile)
            .filter(
                EmployeeProfile.plant_id == source.id,
                EmployeeProfile.is_active.is_(True),
            )
            .all()
        )

        new_login = f"{source.login_id}-copy-{int(time.time())}"
        return self.create_plant(
            db,
            PlantCreate(
                code=source.code,
                name=f"{source.name} (Copy)",
                login_id=new_login,
                password="ChangeMe123!",
                app_role=source.app_role,
                address=source.address,
                linked_scrapeyard_plant_id=source.linked_scrapeyard_plant_id,
                employee_names=[e.name for e in employees],
            ),
        )


plant_service = PlantService()
