import logging

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.general_property import GeneralProperty
from app.schemas.pipeline import PipelineCreate, Pipeline
from app.services.pipeline import pipeline_service

router = APIRouter(prefix="/v1/pipeline", tags=["pipeline"])

logger = logging.getLogger(__name__)


@router.post("/new", response_model=Pipeline, status_code=201)
async def create_pipeline(
        pipeline: PipelineCreate,
        db: Session = Depends(get_db)
):
    """Create a new pipeline."""
    return pipeline_service.create(db, obj_in=pipeline)


@router.get("/all")
async def get_all_pipelines(db: Session = Depends(get_db)):
    try:
        pipelines = pipeline_service.get_all(db)

        items = []
        for pipeline in pipelines:
            properties = []
            added_property_keys = []

            # Get all properties for this device
            device_properties = db.query(GeneralProperty).filter(
                GeneralProperty.referrer_id == pipeline.id,
                GeneralProperty.property_type == 'pipeline',
                GeneralProperty.is_usable == 1
            ).order_by(GeneralProperty.id.desc()).all()

            # Convert properties to the new format
            for prop in device_properties:
                if prop.property_key + prop.property_label in added_property_keys:
                    continue
                properties.append({
                    "id": prop.id,
                    "property_label": prop.property_label,
                    "property_key": prop.property_key,
                    "property_value": prop.property_value,
                    "created_at": prop.created_at
                })
                added_property_keys.append(prop.property_key + prop.property_label)

            items.append({
                **vars(pipeline),
                "properties": properties
            })

        return {
            "total": len(items),
            "items": items
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching pipelines: {str(e)}"
        )


@router.get("/{pipeline_id}")
async def get_pipeline(
        pipeline_id: int,
        db: Session = Depends(get_db)
):
    try:
        pipeline = pipeline_service.get_or_404(db, pipeline_id)

        properties = []
        # Get all properties for this pipeline
        pipeline_properties = db.query(GeneralProperty).filter(
            GeneralProperty.referrer_id == pipeline_id,
            GeneralProperty.property_type == 'pipeline',
            GeneralProperty.is_usable == 1
        ).all()

        # Convert properties to the new format
        for prop in pipeline_properties:
            properties.append({
                "id": prop.id,
                "property_label": prop.property_label,
                "property_key": prop.property_key,
                "property_value": prop.property_value,
                "created_at": prop.created_at
            })

        return {
            **vars(pipeline),
            "properties": properties
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching the pipeline: {str(e)}"
        )


@router.patch("/{pipeline_id}", response_model=Pipeline)
async def update_pipeline(
        pipeline_id: int,
        pipeline: PipelineCreate,
        db: Session = Depends(get_db)
):
    """Update an existing pipeline."""
    db_obj = pipeline_service.get_or_404(db, pipeline_id)
    return pipeline_service.update(db, db_obj=db_obj, obj_in=pipeline)


@router.delete("/{pipeline_id}", response_model=Pipeline)
async def delete_pipeline(
        pipeline_id: int,
        db: Session = Depends(get_db)
):
    """Soft delete a pipeline."""
    return pipeline_service.remove(db, id=pipeline_id)
