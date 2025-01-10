from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import time
from database.connection import get_db
from models.application_session_unit_output import ApplicationSessionUnitOutput
from schemas.application_session_unit_output import ApplicationSessionUnitOutputCreate, ApplicationSessionUnitOutputResponse

router = APIRouter(prefix="/application-session-unit-outputs", tags=["application_session_unit_outputs"])

@router.post("/", response_model=ApplicationSessionUnitOutputResponse)
def create_unit_output(output: ApplicationSessionUnitOutputCreate, db: Session = Depends(get_db)):
    db_output = ApplicationSessionUnitOutput(**output.dict(), created_at=int(time.time()))
    db.add(db_output)
    db.commit()
    db.refresh(db_output)
    return db_output

@router.get("/{output_id}", response_model=ApplicationSessionUnitOutputResponse)
def get_unit_output(output_id: int, db: Session = Depends(get_db)):
    output = db.query(ApplicationSessionUnitOutput).filter(ApplicationSessionUnitOutput.id == output_id).first()
    if not output:
        raise HTTPException(status_code=404, detail="Unit output not found")
    return output

@router.get("/", response_model=List[ApplicationSessionUnitOutputResponse])
def list_unit_outputs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    outputs = db.query(ApplicationSessionUnitOutput).offset(skip).limit(limit).all()
    return outputs

@router.put("/{output_id}", response_model=ApplicationSessionUnitOutputResponse)
def update_unit_output(output_id: int, output: ApplicationSessionUnitOutputCreate, db: Session = Depends(get_db)):
    db_output = db.query(ApplicationSessionUnitOutput).filter(ApplicationSessionUnitOutput.id == output_id).first()
    if not db_output:
        raise HTTPException(status_code=404, detail="Unit output not found")
    
    for key, value in output.dict().items():
        setattr(db_output, key, value)
    
    db.commit()
    db.refresh(db_output)
    return db_output

@router.delete("/{output_id}")
def delete_unit_output(output_id: int, db: Session = Depends(get_db)):
    db_output = db.query(ApplicationSessionUnitOutput).filter(ApplicationSessionUnitOutput.id == output_id).first()
    if not db_output:
        raise HTTPException(status_code=404, detail="Unit output not found")
    
    db_output.is_usable = 0
    db.commit()
    return {"message": "Unit output deleted"}