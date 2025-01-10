from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import time
from database.connection import get_db
from models.general_property import GeneralProperty
from schemas.general_property import GeneralPropertyBase, GeneralPropertyResponse

router = APIRouter(prefix="/general-properties", tags=["general_properties"])

@router.post("/", response_model=GeneralPropertyResponse)
def create_general_property(general_property: GeneralPropertyBase, db: Session = Depends(get_db)):
    db_general_property = GeneralProperty(**general_property.dict(), created_at=int(time.time()))
    db.add(db_general_property)
    db.commit()
    db.refresh(db_general_property)
    return db_general_property

@router.get("/{property_id}", response_model=GeneralPropertyResponse)
def get_general_property(property_id: int, db: Session = Depends(get_db)):
    property = db.query(GeneralProperty).filter(GeneralProperty.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")
    return property

@router.get("/", response_model=List[GeneralPropertyResponse])
def list_general_properties(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    properties = db.query(GeneralProperty).offset(skip).limit(limit).all()
    return properties

@router.put("/{property_id}", response_model=GeneralPropertyResponse)
def update_general_property(property_id: int, general_property: GeneralPropertyBase, db: Session = Depends(get_db)):
    db_property = db.query(GeneralProperty).filter(GeneralProperty.id == property_id).first()
    if not db_property:
        raise HTTPException(status_code=404, detail="Property not found")
    
    for key, value in general_property.dict().items():
        setattr(db_property, key, value)
    
    db.commit()
    db.refresh(db_property)
    return db_property

@router.delete("/{property_id}")
def delete_general_property(property_id: int, db: Session = Depends(get_db)):
    db_property = db.query(GeneralProperty).filter(GeneralProperty.id == property_id).first()
    if not db_property:
        raise HTTPException(status_code=404, detail="Property not found")
    
    db_property.is_usable = 0
    db.commit()
    return {"message": "Property deleted"}