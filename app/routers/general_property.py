import logging
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.auth import require_roles
from app.database.connection import get_db
from app.models.general_property import GeneralProperty
from app.schemas.general_property import GeneralPropertyBase, GeneralPropertyUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/general-property", tags=["General Property"])


@router.get("/all")
async def get_all_properties(
    property_type: Optional[str] = "%",
    property_key: Optional[str] = "%",
    property_value: Optional[str] = "%",
    referrer_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    try:
        # Build base query with filters
        base_filters = [
            GeneralProperty.property_key.like(property_key),
            GeneralProperty.property_type.like(property_type),
            GeneralProperty.property_value.like(property_value),
            GeneralProperty.is_usable == 1,
        ]

        # Add referrer_id filter if provided
        if referrer_id is not None:
            base_filters.append(GeneralProperty.referrer_id == referrer_id)

        properties_subquery = (
            db.query(
                GeneralProperty.property_label,
                func.max(GeneralProperty.id).label("max_id"),
            )
            .filter(*base_filters)
            .group_by(GeneralProperty.property_label)
            .subquery()
        )

        properties = (
            db.query(GeneralProperty)
            .join(
                properties_subquery, GeneralProperty.id == properties_subquery.c.max_id
            )
            .all()
        )

        property_list = [
            {
                "id": prop.id,
                "referrer_id": prop.referrer_id,
                "property_type": prop.property_type,
                "description": f"Property for {prop.property_label}",
                "property_label": prop.property_label,
                "property_key": prop.property_key,
                "property_value": prop.property_value,
                "property_value_type": "string",
                "created_at": prop.created_at,
            }
            for prop in properties
        ]

        return {"total": len(property_list), "properties": property_list}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching properties: {str(e)}"
        )


@router.get("/{general_property_id}")
async def get_pipeline_session_output_unit(
        general_property_id: int,
        db: Session = Depends(get_db),
        _: bool = Depends(require_roles(["app_admin", "app_user"])),
):
    try:
        general_property = db.query(GeneralProperty).filter(GeneralProperty.id == general_property_id).first()

        if not general_property:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline session output unit with ID {general_property} not found",
            )

        return general_property

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching general property: {str(e)}",
        )


@router.post("/new", status_code=201)
async def create_general_property(
    general_property_payload: GeneralPropertyBase, db: Session = Depends(get_db)
):
    try:
        # Create new general property
        new_general_property = GeneralProperty(
            **general_property_payload.model_dump(), created_at=int(time.time())
        )

        db.add(new_general_property)
        db.commit()
        db.refresh(new_general_property)

        return new_general_property

    except HTTPException as he:
        # Handle HTTP exceptions separately
        db.rollback()
        raise he
    except Exception as e:
        logger.error(f"Error in create_pipeline: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error creating pipeline: {str(e)}"
        )


@router.patch("/{general_property_id}/update")
async def update_general_property(
    general_property_id: int,
    general_property_update_payload: GeneralPropertyUpdate,
    db: Session = Depends(get_db),
):
    existing_general_property = db.query(GeneralProperty).filter(
        GeneralProperty.id == general_property_id
    )

    if not existing_general_property.first():
        raise HTTPException(
            status_code=404,
            detail=f"General property with ID {general_property_id} not found",
        )

    existing_general_property.update(
        {
            GeneralProperty.property_value: general_property_update_payload.property_value,
            GeneralProperty.created_at: time.time(),
        }
    )
    db.commit()

    return
