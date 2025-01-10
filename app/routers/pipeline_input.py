from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import time
from database.connection import get_db
from models.pipeline_input import PipelineInput
from schemas.pipeline_input import PipelineInputBase, PipelineInputResponse

router = APIRouter(prefix="/pipeline-inputs", tags=["pipeline_inputs"])

@router.post("/", response_model=PipelineInputResponse)
def create_pipeline_input(pipeline_input: PipelineInputBase, db: Session = Depends(get_db)):
    db_pipeline_input = PipelineInput(**pipeline_input.dict(), created_at=int(time.time()))
    db.add(db_pipeline_input)
    db.commit()
    db.refresh(db_pipeline_input)
    return db_pipeline_input

@router.get("/{input_id}", response_model=PipelineInputResponse)
def get_pipeline_input(input_id: int, db: Session = Depends(get_db)):
    pipeline_input = db.query(PipelineInput).filter(PipelineInput.id == input_id).first()
    if not pipeline_input:
        raise HTTPException(status_code=404, detail="Pipeline input not found")
    return pipeline_input

@router.get("/", response_model=List[PipelineInputResponse])
def list_pipeline_inputs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    pipeline_inputs = db.query(PipelineInput).offset(skip).limit(limit).all()
    return pipeline_inputs

@router.put("/{input_id}", response_model=PipelineInputResponse)
def update_pipeline_input(input_id: int, pipeline_input: PipelineInputBase, db: Session = Depends(get_db)):
    db_pipeline_input = db.query(PipelineInput).filter(PipelineInput.id == input_id).first()
    if not db_pipeline_input:
        raise HTTPException(status_code=404, detail="Pipeline input not found")
    
    for key, value in pipeline_input.dict().items():
        setattr(db_pipeline_input, key, value)
    
    db.commit()
    db.refresh(db_pipeline_input)
    return db_pipeline_input

@router.delete("/{input_id}")
def delete_pipeline_input(input_id: int, db: Session = Depends(get_db)):
    db_pipeline_input = db.query(PipelineInput).filter(PipelineInput.id == input_id).first()
    if not db_pipeline_input:
        raise HTTPException(status_code=404, detail="Pipeline input not found")
    
    db_pipeline_input.is_usable = 0
    db.commit()
    return {"message": "Pipeline input deleted"}