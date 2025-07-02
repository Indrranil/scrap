import logging
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.general_property import GeneralProperty
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


@router.get("/all")
async def get_all_pipeline_input(db: Session = Depends(get_db)):
    try:
        pipeline_inputs = db.query(PipelineInput).filter(
            PipelineInput.is_usable == 1
        ).all()

        items = []
        for pipeline_input in pipeline_inputs:
            properties = []

            # Get all properties for this device
            pipeline_input_properties = db.query(GeneralProperty).filter(
                GeneralProperty.referrer_id == pipeline_input.id,
                GeneralProperty.property_type == 'pipeline_input',
                GeneralProperty.is_usable == 1
            ).all()

            # Convert properties to the new format
            for prop in pipeline_input_properties:
                properties.append({
                    "id": prop.id,
                    "property_label": prop.property_label,
                    "property_key": prop.property_key,
                    "property_value": prop.property_value,
                    "created_at": prop.created_at
                })

            items.append({
                **vars(pipeline_input),
                "properties": properties
            })

        return {
            "total": len(items),
            "items": items
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching pipeline inputs: {str(e)}"
        )


@router.get("/{pipeline_input_id}")
async def get_all_pipeline_input(pipeline_input_id: int, db: Session = Depends(get_db)):
    try:
        pipeline_input = db.query(PipelineInput).filter(
            PipelineInput.is_usable == 1,
            PipelineInput.id == pipeline_input_id
        ).first()

        if not pipeline_input:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline input with ID {pipeline_input_id} not found"
            )

        properties = []

        # Get all properties for this device
        pipeline_input_properties = db.query(GeneralProperty).filter(
            GeneralProperty.referrer_id == pipeline_input.id,
            GeneralProperty.property_type == 'pipeline_input',
            GeneralProperty.is_usable == 1
        ).all()

        # Convert properties to the new format
        for prop in pipeline_input_properties:
            properties.append({
                "id": prop.id,
                "property_label": prop.property_label,
                "property_key": prop.property_key,
                "property_value": prop.property_value,
                "created_at": prop.created_at
            })

        return {
            **vars(pipeline_input),
            "properties": properties
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching pipeline inputs: {str(e)}"
        )
