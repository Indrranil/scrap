from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.connection import get_db
from app.models.general_property import GeneralProperty

router = APIRouter(prefix="/v1/general-property", tags=["General Property"])


@router.get("/")
async def get_all_properties(
        property_type: Optional[str] = "%",
        property_key: Optional[str] = "%",
        property_value: Optional[str] = "%",
        db: Session = Depends(get_db)
):
    try:

        properties_subquery = (
            db.query(
                GeneralProperty.property_label,
                func.min(GeneralProperty.id).label("min_id")
            )
            .filter(
                GeneralProperty.property_key.like(property_key),
                GeneralProperty.property_type.like(property_type),
                GeneralProperty.property_value.like(property_value),
                GeneralProperty.is_usable == 1
            )
            .group_by(GeneralProperty.property_label)
            .subquery()
        )

        properties = (
            db.query(GeneralProperty)
            .join(
                properties_subquery,
                GeneralProperty.id == properties_subquery.c.min_id
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
                "property_value_type": "string",
                "created_at": prop.created_at
            }
            for prop in properties
        ]

        return {
            "total": len(property_list),
            "properties": property_list
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching properties: {str(e)}"
        )
