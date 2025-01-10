from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import time

from database.connection import get_db
from models.application_session import ApplicationSession
from schemas.application_session import ApplicationSessionBase, ApplicationSessionResponse

router = APIRouter(prefix="/application-sessions", tags=["application-sessions"])

@router.post("/", response_model=ApplicationSessionResponse)
def create_session(session: ApplicationSessionBase, db: Session = Depends(get_db)):
   db_session = ApplicationSession(**session.dict(), created_at=int(time.time()))
   db.add(db_session)
   db.commit()
   db.refresh(db_session)
   return db_session

@router.get("/{session_id}", response_model=ApplicationSessionResponse)
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(ApplicationSession).filter(ApplicationSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.put("/{session_id}", response_model=ApplicationSessionResponse)
def update_session(session_id: int, session: ApplicationSessionBase, db: Session = Depends(get_db)):
    db_session = db.query(ApplicationSession).filter(ApplicationSession.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    for key, value in session.dict().items():
        setattr(db_session, key, value)
    db.commit()
    return db_session

@router.delete("/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):
    db_session = db.query(ApplicationSession).filter(ApplicationSession.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(db_session)
    db.commit()
    return {"message": "Session deleted"}