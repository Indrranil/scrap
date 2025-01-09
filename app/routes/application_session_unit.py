from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import time
from database.connection import get_db
from models.application_session_unit import ApplicationSessionUnit
from schemas.application_session_unit import ApplicationSessionUnitBase, ApplicationSessionUnitResponse

router = APIRouter(prefix="/application-session-units", tags=["application_session_units"])

@router.post("/", response_model=ApplicationSessionUnitResponse)
def create_session_unit(unit: ApplicationSessionUnitBase, db: Session = Depends(get_db)):
    db_unit = ApplicationSessionUnit(**unit.dict(), created_at=int(time.time()))
    db.add(db_unit)
    db.commit()
    db.refresh(db_unit)
    return db_unit

@router.get("/{unit_id}", response_model=ApplicationSessionUnitResponse)
def get_session_unit(unit_id: int, db: Session = Depends(get_db)):
    unit = db.query(ApplicationSessionUnit).filter(ApplicationSessionUnit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Session unit not found")
    return unit

@router.get("/", response_model=List[ApplicationSessionUnitResponse])
def list_session_units(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    units = db.query(ApplicationSessionUnit).offset(skip).limit(limit).all()
    return units

@router.put("/{unit_id}", response_model=ApplicationSessionUnitResponse)
def update_session_unit(unit_id: int, unit: ApplicationSessionUnitBase, db: Session = Depends(get_db)):
    db_unit = db.query(ApplicationSessionUnit).filter(ApplicationSessionUnit.id == unit_id).first()
    if not db_unit:
        raise HTTPException(status_code=404, detail="Session unit not found")
    
    for key, value in unit.dict().items():
        setattr(db_unit, key, value)
    
    db.commit()
    db.refresh(db_unit)
    return db_unit

@router.delete("/{unit_id}")
def delete_session_unit(unit_id: int, db: Session = Depends(get_db)):
    db_unit = db.query(ApplicationSessionUnit).filter(ApplicationSessionUnit.id == unit_id).first()
    if not db_unit:
        raise HTTPException(status_code=404, detail="Session unit not found")
    
    db_unit.is_usable = 0
    db.commit()
    return {"message": "Session unit deleted"}