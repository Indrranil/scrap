from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import time
from database.connection import get_db
from models.pipeline_input_referrer import PipelineInputReferrer
from schemas.pipeline_input_referrer import PipelineInputReferrerBase, PipelineInputReferrerResponse

router = APIRouter(prefix="/pipeline-input-referrers", tags=["pipeline_input_referrers"])

@router.post("/", response_model=PipelineInputReferrerResponse)
def create_pipeline_input_referrer(referrer: PipelineInputReferrerBase, db: Session = Depends(get_db)):
    db_referrer = PipelineInputReferrer(**referrer.dict(), created_at=int(time.time()))
    db.add(db_referrer)
    db.commit()
    db.refresh(db_referrer)
    return db_referrer

@router.get("/{referrer_id}", response_model=PipelineInputReferrerResponse)
def get_pipeline_input_referrer(referrer_id: int, db: Session = Depends(get_db)):
    referrer = db.query(PipelineInputReferrer).filter(PipelineInputReferrer.id == referrer_id).first()
    if not referrer:
        raise HTTPException(status_code=404, detail="Referrer not found")
    return referrer

@router.get("/", response_model=List[PipelineInputReferrerResponse])
def list_pipeline_input_referrers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    referrers = db.query(PipelineInputReferrer).offset(skip).limit(limit).all()
    return referrers

@router.put("/{referrer_id}", response_model=PipelineInputReferrerResponse)
def update_pipeline_input_referrer(referrer_id: int, referrer: PipelineInputReferrerBase, db: Session = Depends(get_db)):
    db_referrer = db.query(PipelineInputReferrer).filter(PipelineInputReferrer.id == referrer_id).first()
    if not db_referrer:
        raise HTTPException(status_code=404, detail="Referrer not found")
    
    for key, value in referrer.dict().items():
        setattr(db_referrer, key, value)
    
    db.commit()
    db.refresh(db_referrer)
    return db_referrer

@router.delete("/{referrer_id}")
def delete_pipeline_input_referrer(referrer_id: int, db: Session = Depends(get_db)):
    db_referrer = db.query(PipelineInputReferrer).filter(PipelineInputReferrer.id == referrer_id).first()
    if not db_referrer:
        raise HTTPException(status_code=404, detail="Referrer not found")
    
    db_referrer.is_usable = 0
    db.commit()
    return {"message": "Referrer deleted"}