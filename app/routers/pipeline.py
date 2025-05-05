import logging
import time
from typing import List

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.pipeline import Pipeline as PipelineModel
from app.schemas.pipeline import PipelineCreate, Pipeline

router = APIRouter(prefix="/v1/pipeline", tags=["pipeline"])

logger = logging.getLogger(__name__)


@router.post("/new", response_model=Pipeline, status_code=201)
async def create_pipeline(
        pipeline: PipelineCreate,
        db: Session = Depends(get_db)
):
    try:
        logger.debug(f"Creating pipeline with data: {pipeline.dict()}")

        # # Check for duplicate name
        # if check_duplicate_name(db, pipeline.name):
        #     logger.debug("Duplicate name found")
        #     raise HTTPException(
        #         status_code=400,
        #         detail="Pipeline with this name already exists"
        #     )

        # Create new pipeline
        new_pipeline = PipelineModel(
            name=pipeline.name,
            is_running=pipeline.is_running,
            application_id=pipeline.application_id,
            created_at=int(time.time()),
            is_usable=pipeline.is_usable
        )
        logger.debug(f"Created model instance: {vars(new_pipeline)}")

        db.add(new_pipeline)
        db.commit()
        logger.debug("Database commit successful")
        db.refresh(new_pipeline)
        logger.debug(f"Refreshed model instance: {vars(new_pipeline)}")

        return new_pipeline

    except HTTPException as he:
        # Handle HTTP exceptions separately
        db.rollback()
        raise he
    except Exception as e:
        logger.error(f"Error in create_pipeline: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating pipeline: {str(e)}"
        )


@router.get("/all", response_model=List[Pipeline])
async def get_all_pipelines(db: Session = Depends(get_db)):
    try:
        pipelines = db.query(PipelineModel).filter(
            PipelineModel.is_usable == 1
        ).all()

        return pipelines

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching pipelines: {str(e)}"
        )


@router.get("/{pipeline_id}", response_model=Pipeline)
async def get_pipeline(
        pipeline_id: int,
        db: Session = Depends(get_db)
):
    try:
        pipeline = db.query(PipelineModel).filter(
            PipelineModel.id == pipeline_id,
            PipelineModel.is_usable == 1
        ).first()

        if not pipeline:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline with ID {pipeline_id} not found"
            )

        return pipeline

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching pipeline: {str(e)}"
        )


@router.patch("/{pipeline_id}", response_model=Pipeline)
async def update_pipeline(
        pipeline_id: int,
        pipeline: PipelineCreate,
        db: Session = Depends(get_db)
):
    try:
        existing_pipeline = db.query(PipelineModel).filter(
            PipelineModel.id == pipeline_id,
            PipelineModel.is_usable == 1
        ).first()

        if not existing_pipeline:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline with ID {pipeline_id} not found"
            )

        # # Check for duplicate name
        # if check_duplicate_name(db, pipeline.name, exclude_id=pipeline_id):
        #     raise HTTPException(
        #         status_code=400,
        #         detail="Pipeline with this name already exists"
        #     )

        # Update fields using setattr
        setattr(existing_pipeline, 'name', pipeline.name)
        setattr(existing_pipeline, 'is_usable', pipeline.is_usable)

        db.commit()
        db.refresh(existing_pipeline)

        return existing_pipeline

    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error updating pipeline: {str(e)}"
        )


@router.delete("/{pipeline_id}")
async def delete_pipeline(
        pipeline_id: int,
        db: Session = Depends(get_db)
):
    try:
        db.begin()

        pipeline = db.query(PipelineModel).filter(
            PipelineModel.id == pipeline_id,
            PipelineModel.is_usable == 1
        ).first()

        if not pipeline:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline with ID {pipeline_id} not found"
            )

        # Soft delete
        pipeline.is_usable = 0

        db.commit()

        return {
            "message": f"Pipeline with ID {pipeline_id} successfully deleted"
        }

    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting pipeline: {str(e)}"
        )
