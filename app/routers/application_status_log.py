from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import time
from database.connection import get_db
from models.application_status_log import ApplicationStatusLog
from schemas.application_status_log import ApplicationStatusLogCreate, ApplicationStatusLogResponse

router = APIRouter(prefix="/application-status-logs", tags=["application_status_logs"])

@router.post("/", response_model=ApplicationStatusLogResponse)
def create_status_log(status_log: ApplicationStatusLogCreate, db: Session = Depends(get_db)):
    db_status_log = ApplicationStatusLog(**status_log.dict(), created_at=int(time.time()))
    db.add(db_status_log)
    db.commit()
    db.refresh(db_status_log)
    return db_status_log

@router.get("/{log_id}", response_model=ApplicationStatusLogResponse)
def get_status_log(log_id: int, db: Session = Depends(get_db)):
    status_log = db.query(ApplicationStatusLog).filter(ApplicationStatusLog.id == log_id).first()
    if not status_log:
        raise HTTPException(status_code=404, detail="Status log not found")
    return status_log

@router.get("/", response_model=List[ApplicationStatusLogResponse])
def list_status_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    status_logs = db.query(ApplicationStatusLog).offset(skip).limit(limit).all()
    return status_logs

@router.get("/container/{container_id}", response_model=List[ApplicationStatusLogResponse])
def get_container_status_logs(container_id: str, db: Session = Depends(get_db)):
    status_logs = db.query(ApplicationStatusLog).filter(
        ApplicationStatusLog.application_container_id == container_id
    ).order_by(ApplicationStatusLog.created_at.desc()).all()
    return status_logs

@router.put("/{log_id}",response_model=ApplicationStatusLogResponse)
def update_status_log(log_id:int,status_log:ApplicationStatusLogCreate,db: Session = Depends(get_db)):
    db_status = db.query(ApplicationStatusLog).filter(ApplicationStatusLog.id == log_id).first()
    if not status_log:
        raise HTTPException(status_code=404, detail="Status log not found")
    for key,value in status_log.dict().items():
        setattr(db_status,key,value)
    db.commit()
    db.refresh(db_status)
    return db_status

@router.delete("/{log_id}")
def delete_status_log(log_id:int,db: Session = Depends(get_db)):
    db_status = db.query(ApplicationStatusLog).filter(ApplicationStatusLog.id == log_id).first()
    if not status_log:
        raise HTTPException(status_code=404, detail="Status log not found")
    
    db.delete(db_status)
    db.commit()
    return {"Message":"Status Log deleted successfully"}
