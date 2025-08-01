import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.pipeline_input import PipelineInputBase, PipelineInputResponse
from app.services.pipeline_input import pipeline_input_service

router = APIRouter(prefix="/v1/pipeline-input", tags=["Pipeline Input"])

logger = logging.getLogger(__name__)


@router.post("/new", response_model=PipelineInputResponse, status_code=201)
async def create_pipeline_input(
    pipeline_input: PipelineInputBase, db: Session = Depends(get_db)
):
    """Create a new pipeline input."""
    return pipeline_input_service.create(db, obj_in=pipeline_input)


@router.get("/all")
async def get_all_pipeline_input(db: Session = Depends(get_db)):
    """Get all active pipeline inputs."""
    try:
        pipeline_inputs = pipeline_input_service.get_all(db)

        items = []
        for pipeline_input in pipeline_inputs:
            items.append(
                {
                    "id": pipeline_input.id,
                    "name": pipeline_input.name,
                    "created_at": pipeline_input.created_at,
                    "is_usable": pipeline_input.is_usable,
                }
            )

        return {"total": len(items), "items": items}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching pipeline inputs: {str(e)}"
        )


@router.get("/{pipeline_input_id}", response_model=PipelineInputResponse)
async def get_pipeline_input(pipeline_input_id: int, db: Session = Depends(get_db)):
    """Get a specific pipeline input by ID."""
    return pipeline_input_service.get_or_404(db, pipeline_input_id)


@router.patch("/{pipeline_input_id}", response_model=PipelineInputResponse)
async def update_pipeline_input(
    pipeline_input_id: int,
    pipeline_input: PipelineInputBase,
    db: Session = Depends(get_db),
):
    """Update an existing pipeline input."""
    db_obj = pipeline_input_service.get_or_404(db, pipeline_input_id)
    return pipeline_input_service.update(db, db_obj=db_obj, obj_in=pipeline_input)


@router.delete("/{pipeline_input_id}", response_model=PipelineInputResponse)
async def delete_pipeline_input(pipeline_input_id: int, db: Session = Depends(get_db)):
    """Soft delete a pipeline input."""
    return pipeline_input_service.remove(db, id=pipeline_input_id)
