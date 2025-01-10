from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import time
from database.connection import get_db
from models.application_output_type import ApplicationOutputType
from schemas.application_output_type import ApplicationOutputTypeCreate, ApplicationOutputTypeResponse

router = APIRouter(prefix="/application-output-types", tags=["application_output_types"])

@router.post("/", response_model=ApplicationOutputTypeResponse)
def create_output_type(output_type: ApplicationOutputTypeCreate, db: Session = Depends(get_db)):
    db_output_type = ApplicationOutputType(**output_type.dict(), created_at=int(time.time()))
    db.add(db_output_type)
    db.commit()
    db.refresh(db_output_type)
    return db_output_type

@router.get("/{output_type_id}", response_model=ApplicationOutputTypeResponse)
def get_output_type(output_type_id: int, db: Session = Depends(get_db)):
    output_type = db.query(ApplicationOutputType).filter(ApplicationOutputType.id == output_type_id).first()
    if not output_type:
        raise HTTPException(status_code=404, detail="Output type not found")
    return output_type

@router.get("/", response_model=List[ApplicationOutputTypeResponse])
def list_output_types(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    output_types = db.query(ApplicationOutputType).offset(skip).limit(limit).all()
    return output_types

@router.get("/application/{application_id}", response_model=List[ApplicationOutputTypeResponse])
def get_application_output_types(application_id: int, db: Session = Depends(get_db)):
    output_types = db.query(ApplicationOutputType).filter(
        ApplicationOutputType.application_id == application_id,
        ApplicationOutputType.is_usable == 1
    ).all()
    return output_types

@router.put("/{output_type_id}", response_model=ApplicationOutputTypeResponse)
def update_output_type(output_type_id: int, output_type: ApplicationOutputTypeCreate, db: Session = Depends(get_db)):
    db_output_type = db.query(ApplicationOutputType).filter(ApplicationOutputType.id == output_type_id).first()
    if not db_output_type:
        raise HTTPException(status_code=404, detail="Output type not found")
    
    for key, value in output_type.dict().items():
        setattr(db_output_type, key, value)
    
    db.commit()
    db.refresh(db_output_type)
    return db_output_type

@router.delete("/{output_type_id}")
def delete_output_type(output_type_id: int, db: Session = Depends(get_db)):
    db_output_type = db.query(ApplicationOutputType).filter(ApplicationOutputType.id == output_type_id).first()
    if not db_output_type:
        raise HTTPException(status_code=404, detail="Output type not found")
    
    db_output_type.is_usable = 0
    db.commit()
    return {"message": "Output type deleted"}