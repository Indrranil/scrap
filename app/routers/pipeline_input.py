import logging
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.pipeline_input import PipelineInput
from app.schemas.pipeline_input import PipelineInputBase

router = APIRouter(prefix="/v1/pipeline-input", tags=["Pipeline Input"])

logger = logging.getLogger(__name__)


@router.post("/new", status_code=201)
async def create_pipeline_input(pipeline: PipelineInputBase, db: Session = Depends(get_db)):
    try:
        # Create new pipeline
        new_pipeline = PipelineInput(
            name=pipeline.name,
            created_at=int(time.time()),
            is_usable=pipeline.is_usable
        )

        db.add(new_pipeline)
        db.commit()
        db.refresh(new_pipeline)

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
