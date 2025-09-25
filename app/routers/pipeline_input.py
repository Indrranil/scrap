import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.general_property import GeneralProperty
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
    """Get all active pipeline inputs with their general properties."""
    try:
        pipeline_inputs = pipeline_input_service.get_all(db)

        items = []
        for pipeline_input in pipeline_inputs:
            # Get all properties for this pipeline input
            properties = (
                db.query(GeneralProperty)
                .filter(
                    GeneralProperty.referrer_id == pipeline_input.id,
                    GeneralProperty.property_type == "pipeline_input",
                    GeneralProperty.is_usable == 1,
                )
                .all()
            )

            # Format properties
            properties_list = []
            for prop in properties:
                properties_list.append({
                    "id": prop.id,
                    "property_label": prop.property_label,
                    "property_key": prop.property_key,
                    "property_value": prop.property_value,
                    "created_at": prop.created_at,
                })

            items.append(
                {
                    "id": pipeline_input.id,
                    "name": pipeline_input.name,
                    "created_at": pipeline_input.created_at,
                    "is_usable": pipeline_input.is_usable,
                    "properties": properties_list,
                }
            )

        return {"total": len(items), "items": items}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching pipeline inputs: {str(e)}"
        )


@router.get("/{pipeline_input_id}")
async def get_pipeline_input(pipeline_input_id: int, db: Session = Depends(get_db)):
    """Get a specific pipeline input by ID with its general properties."""
    try:
        pipeline_input = pipeline_input_service.get_or_404(db, pipeline_input_id)

        # Get all properties for this pipeline input
        properties = (
            db.query(GeneralProperty)
            .filter(
                GeneralProperty.referrer_id == pipeline_input.id,
                GeneralProperty.property_type == "pipeline_input",
                GeneralProperty.is_usable == 1,
            )
            .all()
        )

        # Format properties
        properties_list = []
        for prop in properties:
            properties_list.append({
                "id": prop.id,
                "property_label": prop.property_label,
                "property_key": prop.property_key,
                "property_value": prop.property_value,
                "created_at": prop.created_at,
            })

        return {
            "id": pipeline_input.id,
            "name": pipeline_input.name,
            "created_at": pipeline_input.created_at,
            "is_usable": pipeline_input.is_usable,
            "properties": properties_list,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching pipeline input: {str(e)}"
        )


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
