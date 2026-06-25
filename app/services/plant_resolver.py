from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.plant import Plant


def resolve_plant_by_qr_location(db: Session, location: int) -> Plant:
    plant = (
        db.query(Plant)
        .filter(Plant.qr_location == location, Plant.is_active.is_(True))
        .first()
    )
    if not plant:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown QR location: {location}",
        )
    return plant
