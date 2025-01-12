from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from typing import List
import time
from database.connection import get_db
from models.pipeline import Pipeline
from schemas.pipeline import PipelineBase, PipelineResponse
from auth.rbac import require_permission

router = APIRouter(prefix="/pipelines", tags=["pipelines"])

@router.get("/", response_model=List[PipelineResponse])
async def list_pipelines(
    db: Session = Depends(get_db),
    _: bool = require_permission("read:pipeline")
):
    pipelines = db.query(Pipeline).filter(Pipeline.is_usable == 1).all()
    return pipelines

@router.get("/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(
    pipeline_id: int,
    db: Session = Depends(get_db),
    _: bool = require_permission("read:pipeline")
):
    pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline

@router.post("/", response_model=PipelineResponse)
async def create_pipeline(
    pipeline: PipelineBase,
    db: Session = Depends(get_db),
    _: bool = require_permission("create:pipeline")
):
    try:
        db_pipeline = Pipeline(**pipeline.dict(), created_at=int(time.time()))
        db.add(db_pipeline)
        db.commit()
        db.refresh(db_pipeline)
        return db_pipeline
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/{pipeline_id}",response_model=PipelineResponse)
async def put_pipeline(
    pipeline_id: int,
    pipeline: PipelineBase,
    db: Session = Depends(get_db),
    _: bool = require_permission("read:pipeline")
):
    db_pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
    if not db_pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    for key,value in pipeline.dict().items():
        setattr(db_pipeline,key,value)
    db.commit()
    db.refresh(db_pipeline)
    return db_pipeline

@router.delete("/{pipeline_id}")
async def delete_pipeline(
    pipeline_id:int,
    db: Session = Depends(get_db),
    _: bool = require_permission("delete:pipeline")
):
    db_pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
    if not db_pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    db.delete(db_pipeline)
    db.commit()
    return {"Message":"Pipeline deleted successfully"}