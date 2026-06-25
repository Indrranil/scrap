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
            qr_location=plant.qr_location,
            address=plant.address,
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
        if db.query(Plant).filter(Plant.login_id == data.login_id).first():
            raise HTTPException(status_code=409, detail="Login ID already exists")
        if db.query(Plant).filter(Plant.qr_location == data.qr_location).first():
            raise HTTPException(status_code=409, detail="QR location already in use")

        plant = Plant(
            code=data.code,
            name=data.name,
            login_id=data.login_id,
            password_hash=hash_password(data.password),
            qr_location=data.qr_location,
            address=data.address,
            is_active=True,
            created_at=int(time.time()),
        )
        db.add(plant)
        db.flush()
        self._sync_employees(db, plant.id, data.employee_names)
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
            if (
                db.query(Plant)
                .filter(Plant.login_id == data.login_id, Plant.id != plant_id)
                .first()
            ):
                raise HTTPException(status_code=409, detail="Login ID already exists")
            plant.login_id = data.login_id

        if data.qr_location is not None and data.qr_location != plant.qr_location:
            if (
                db.query(Plant)
                .filter(Plant.qr_location == data.qr_location, Plant.id != plant_id)
                .first()
            ):
                raise HTTPException(status_code=409, detail="QR location already in use")
            plant.qr_location = data.qr_location

        if data.code is not None:
            plant.code = data.code
        if data.name is not None:
            plant.name = data.name
        if data.password:
            plant.password_hash = hash_password(data.password)
        if data.address is not None:
            plant.address = data.address

        if data.employee_names is not None:
            self._sync_employees(db, plant.id, data.employee_names)

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
                qr_location=source.qr_location + 1000,
                address=source.address,
                employee_names=[e.name for e in employees],
            ),
        )

    def _sync_employees(
        self, db: Session, plant_id: int, names: List[str]
    ) -> None:
        db.query(EmployeeProfile).filter(
            EmployeeProfile.plant_id == plant_id
        ).update({"is_active": False})
        for name in names:
            db.add(
                EmployeeProfile(
                    plant_id=plant_id,
                    name=name,
                    is_active=True,
                    created_at=int(time.time()),
                )
            )


plant_service = PlantService()
