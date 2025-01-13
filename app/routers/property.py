from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from models.general_property import GeneralProperty
from models.pipeline_input_referrer import PipelineInputReferrer


router = APIRouter(prefix="/v1/property-description", tags=["property_description"])

@router.get("/{property_type}")
async def get_properties_by_type(
    property_type: str,
    db: Session = Depends(get_db)
):
    try:
        valid_types = ['machine', 'pipeline', 'application', 'pipeline_input']
        if property_type.lower() not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid property type. Must be one of: {', '.join(valid_types)}"
            )
        properties = (
            db.query(
                GeneralProperty.id,
                GeneralProperty.property_type,
                GeneralProperty.property_label,
                GeneralProperty.property_key,
                GeneralProperty.created_at
            )
            .filter(
                GeneralProperty.property_type == property_type.lower(),
                GeneralProperty.is_usable == 1
            )
            .distinct(
                GeneralProperty.property_label,
                GeneralProperty.property_key
            )
            .all()
        )

        # Format the response
        property_list = [
            {
                "id": prop.id,
                "property_type": prop.property_type,
                "description": f"Property for {prop.property_label}",  # You can customize this or add a description field to your table
                "property_label": prop.property_label,
                "property_key": prop.property_key,
                "created_at": prop.created_at
            }
            for prop in properties
        ]

        # If property_type is pipeline_input, add CLD barcode property
        if property_type.lower() == 'pipeline_input':
            cld_props = (
                db.query(PipelineInputReferrer)
                .filter(
                    PipelineInputReferrer.key == 'cld_barcode',
                    PipelineInputReferrer.is_usable == 1
                )
                .first()
            )
            if cld_props:
                property_list.append({
                    "id": cld_props.id,
                    "property_type": "pipeline_input",
                    "description": "CLD Barcode identifier",
                    "property_label": "CLD Barcode",
                    "property_key": "cld_barcode",
                    "property_value_type": "string",
                    "created_at": cld_props.created_at
                })

        return {
            "total": len(property_list),
            "properties": property_list
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching properties: {str(e)}"
        )