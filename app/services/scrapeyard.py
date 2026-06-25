import time
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.auth.jwt_auth import hash_password
from app.models.employee_profile import EmployeeProfile
from app.models.scrapeyard import Scrapeyard
from app.schemas.auth import EmployeeSummary
from app.schemas.scrapeyard import ScrapeyardResponse, ScrapeyardUpdate


class ScrapeyardService:
    def get_active(self, db: Session) -> Scrapeyard:
        scrapeyard = (
            db.query(Scrapeyard).filter(Scrapeyard.is_active.is_(True)).first()
        )
        if not scrapeyard:
            raise HTTPException(status_code=500, detail="Scrapeyard not configured")
        return scrapeyard

    def to_response(self, db: Session, scrapeyard: Scrapeyard) -> ScrapeyardResponse:
        employees = (
            db.query(EmployeeProfile)
            .filter(
                EmployeeProfile.scrapeyard_id == scrapeyard.id,
                EmployeeProfile.is_active.is_(True),
            )
            .all()
        )
        return ScrapeyardResponse(
            id=scrapeyard.id,
            name=scrapeyard.name,
            login_id=scrapeyard.login_id,
            is_active=scrapeyard.is_active,
            employees=[EmployeeSummary(id=e.id, name=e.name) for e in employees],
        )

    def get_config(self, db: Session) -> ScrapeyardResponse:
        return self.to_response(db, self.get_active(db))

    def update_config(
        self, db: Session, data: ScrapeyardUpdate
    ) -> ScrapeyardResponse:
        scrapeyard = self.get_active(db)

        if data.login_id and data.login_id != scrapeyard.login_id:
            conflict = (
                db.query(Scrapeyard)
                .filter(
                    Scrapeyard.login_id == data.login_id,
                    Scrapeyard.id != scrapeyard.id,
                )
                .first()
            )
            if conflict:
                raise HTTPException(status_code=409, detail="Login ID already exists")
            scrapeyard.login_id = data.login_id

        if data.name is not None:
            scrapeyard.name = data.name
        if data.password:
            scrapeyard.password_hash = hash_password(data.password)

        if data.employee_names is not None:
            db.query(EmployeeProfile).filter(
                EmployeeProfile.scrapeyard_id == scrapeyard.id
            ).update({"is_active": False})
            for name in data.employee_names:
                db.add(
                    EmployeeProfile(
                        scrapeyard_id=scrapeyard.id,
                        name=name,
                        is_active=True,
                        created_at=int(time.time()),
                    )
                )

        db.commit()
        db.refresh(scrapeyard)
        return self.to_response(db, scrapeyard)


scrapeyard_service = ScrapeyardService()
