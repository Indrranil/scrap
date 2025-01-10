from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import time

from database.connection import get_db
from models.application import Application
from schemas.application import ApplicationBase, ApplicationResponse

router = APIRouter(prefix="/applications", tags=["applications"])

@router.post("/", response_model=ApplicationResponse)
def create_application(app: ApplicationBase, db: Session = Depends(get_db)):
   db_app = Application(**app.dict(), created_at=int(time.time()))
   db.add(db_app)
   db.commit()
   db.refresh(db_app)
   return db_app

@router.get("/{app_id}", response_model=ApplicationResponse)
def get_application(app_id: int, db: Session = Depends(get_db)):
   app = db.query(Application).filter(Application.id == app_id).first()
   if not app:
       raise HTTPException(status_code=404, detail="Application not found")
   return app

@router.put("/{app_id}", response_model=ApplicationResponse)
def update_application(app_id: int, app: ApplicationBase, db: Session = Depends(get_db)):
    db_app = db.query(Application).filter(Application.id == app_id).first()
    if not db_app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    for key, value in app.dict().items():
        setattr(db_app, key, value)
    db.commit()
    return db_app

@router.delete("/{app_id}")
def delete_application(app_id: int, db: Session = Depends(get_db)):
    db_app = db.query(Application).filter(Application.id == app_id).first()
    if not db_app:
        raise HTTPException(status_code=404, detail="Application not found")
    db.delete(db_app)
    db.commit()
    return {"message": "Application deleted"}