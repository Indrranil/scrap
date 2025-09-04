import time
from io import StringIO
from typing import Any, Dict, Optional

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.general_property import GeneralProperty
from app.models.pipeline_input import PipelineInput

router = APIRouter(prefix="/v1/admin", tags=["admin"])

# Hardcoded mapping for column_name to property_key
COLUMN_PROPERTY_MAPPING = {
    "Machine Code-Front": "front",
    "Machine Code-Back": "back", 
    "Material Code-Front": "material_front",
    "Material Code-Back": "material_back",
    "Factory Code": "factory_code",
    "Price": "price",
    "USP": "usp",
    "Manufacturing Date": "manufacturing_date",
    "Expiry Date": "expiry_date",
    "Target Weight (g)": "target_weight",
    "Tare Weight (g)": "tare_weight",
    "Form Factor": "form_factor",
    "Product Name": "product_name",
    "Variant Barcode": "variant_barcode",
    "CLD Barcode": "cld_barcode",
    "Front Face": "front_face",
    "Back Face": "back_face", 
    "Left Face": "left_face",
    "Right Face": "right_face",
    "Top Face": "top_face",
    "Bottom Face": "bottom_face",
    "Damage": "damage",
    "Flap Open": "flap_open",
    "Grease Dirt": "grease_dirt",
    "Color Mismatch": "color_mismatch"
}

# Pipeline Input core fields that go directly to PipelineInput table
PIPELINE_INPUT_FIELDS = {"Variant Name"}

# Form field configurations for different form types
FORM_CONFIGURATIONS = {
    "product": {
        "name": "Product Form",
        "description": "Form for creating/editing product variants",
        "fields": [
            {
                "name": "Variant Name",
                "type": "text",
                "required": True
            },
            {
                "name": "Product Name",
                "type": "text",
                "required": False
            },
            {
                "name": "Form Factor",
                "type": "text",
                "required": False
            },
            {
                "name": "Price",
                "type": "float",
                "required": False
            },
            {
                "name": "Target Weight (g)",
                "type": "float",
                "required": False
            },
            {
                "name": "Tare Weight (g)",
                "type": "float",
                "required": False
            },
            {
                "name": "Material Code-Front",
                "type": "text",
                "required": False
            },
            {
                "name": "Material Code-Back",
                "type": "text",
                "required": False
            },
            {
                "name": "Factory Code",
                "type": "text",
                "required": False
            },
            {
                "name": "USP",
                "type": "text",
                "required": False
            },
            {
                "name": "Manufacturing Date",
                "type": "date",
                "required": False
            },
            {
                "name": "Expiry Date",
                "type": "date",
                "required": False
            },
            {
                "name": "Variant Barcode",
                "type": "text",
                "required": False
            },
            {
                "name": "CLD Barcode",
                "type": "text",
                "required": False
            }
        ]
    }
}


def create_pipeline_input_from_data(data: Dict[str, Any], db: Session) -> PipelineInput:
    """Create or get existing PipelineInput from data"""
    variant_name = data.get("Variant Name", "").lower()
    
    if not variant_name:
        raise ValueError("Variant Name is required")
    
    # Check if pipeline input already exists
    pipeline_input = (
        db.query(PipelineInput)
        .filter(
            PipelineInput.name == variant_name,
            PipelineInput.is_usable == 1,
        )
        .first()
    )
    
    if not pipeline_input:
        pipeline_input = PipelineInput(
            name=variant_name,
            created_at=int(time.time()),
            is_usable=1
        )
        db.add(pipeline_input)
        db.flush()
    
    return pipeline_input


def create_general_properties_from_data(
    data: Dict[str, Any], 
    pipeline_input: PipelineInput, 
    db: Session
) -> list:
    """Create GeneralProperty records from remaining data fields"""
    properties_list = []
    timestamp = int(time.time())
    
    for column_name, column_value in data.items():
        # Skip pipeline input fields and empty values
        if column_name in PIPELINE_INPUT_FIELDS or column_value is None or column_value == "":
            continue
            
        # Get property_key from mapping, or empty string if not found
        property_key = COLUMN_PROPERTY_MAPPING.get(column_name, "")
        
        # Create GeneralProperty record
        property_entity = GeneralProperty(
            referrer_id=pipeline_input.id,
            property_type="pipeline_input",
            property_key=property_key,
            property_label=column_name,
            property_value=str(column_value),
            created_at=timestamp,
            is_usable=1,
        )
        db.add(property_entity)
        db.flush()
        
        properties_list.append({
            "id": property_entity.id,
            "property_label": property_entity.property_label,
            "property_key": property_entity.property_key,
            "property_value": property_entity.property_value,
            "created_at": property_entity.created_at,
        })
    
    return properties_list


@router.get("/form-fields")
async def get_all_form_types():
    """Get all available form types"""
    form_types = []
    for form_type, config in FORM_CONFIGURATIONS.items():
        form_types.append({
            "type": form_type,
            "name": config["name"],
            "description": config["description"],
            "field_count": len(config["fields"])
        })
    
    return {
        "total": len(form_types),
        "form_types": form_types
    }


@router.get("/form-fields/{form_type}")
async def get_form_fields(form_type: str, required: Optional[bool] = None):
    """Get form fields configuration for a specific form type"""
    if form_type not in FORM_CONFIGURATIONS:
        raise HTTPException(
            status_code=404, 
            detail=f"Form type '{form_type}' not found. Available types: {list(FORM_CONFIGURATIONS.keys())}"
        )
    
    config = FORM_CONFIGURATIONS[form_type]
    fields = config["fields"]
    
    # Filter by required parameter if provided
    if required is not None:
        fields = [field for field in fields if field.get("required", False) == required]
    
    # Return only name and type for filtered fields
    simplified_fields = [{"name": field["name"], "type": field["type"]} for field in fields]
    
    return {
        "form_type": form_type,
        "name": config["name"],
        "description": config["description"],
        "fields": simplified_fields,
        "total_fields": len(simplified_fields)
    }


@router.post("/product")
async def create_product_upload(
    data: Dict[str, Any],
    db: Session = Depends(get_db),
):
    """Single product upload with dynamic property creation"""
    try:
        db.begin()
        
        # 1. Create/Get Pipeline Input
        pipeline_input = create_pipeline_input_from_data(data, db)
        
        # 2. Create General Properties from remaining fields
        properties_list = create_general_properties_from_data(data, pipeline_input, db)
        
        # Commit transaction
        db.commit()
        
        return {
            "total": 1,
            "items": [
                {
                    "id": pipeline_input.id,
                    "name": pipeline_input.name,
                    "created_at": pipeline_input.created_at,
                    "properties": properties_list,
                }
            ],
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/product/bulk")
async def create_bulk_product_upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Bulk product upload with dynamic property creation from CSV"""
    try:
        contents = await file.read()
        df = pd.read_csv(StringIO(contents.decode("utf-8")))
        
        # Handle unnamed columns by using first non-empty row as headers
        if all(col.startswith("Unnamed:") for col in df.columns):
            # Find the first non-empty row to use as headers
            header_row_index = 0
            for i, row in df.iterrows():
                if not all(pd.isna(val) or str(val).strip() == "" for val in row):
                    header_row_index = i
                    break
            
            headers = df.iloc[header_row_index].tolist()
            # Skip empty rows and header row, start from data rows
            df = pd.read_csv(
                StringIO(contents.decode("utf-8")), 
                skiprows=header_row_index + 1,
                names=headers
            )
            # Clean the dataframe to remove any remaining empty rows
            df = df.dropna(how='all')
        # For normal CSVs with proper headers, pandas handles it correctly
        
        # Check required columns
        required_columns = ["Variant Name"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_columns)}",
            )
        
        successful_items = []
        failed_items = []
        
        for index, row in df.iterrows():
            try:
                with db.begin_nested():
                    # Convert row to dictionary, handling NaN values
                    row_data = {}
                    for col in df.columns:
                        value = row[col]
                        if pd.notna(value) and value != "" and str(value).strip() != "":
                            # Handle potential float conversion issues
                            if isinstance(value, float):
                                if not (value == float('inf') or value == float('-inf') or value != value):
                                    row_data[col] = value
                            else:
                                row_data[col] = value
                    
                    # 1. Create/Get Pipeline Input
                    pipeline_input = create_pipeline_input_from_data(row_data, db)
                    
                    # 2. Create General Properties from remaining fields
                    properties_list = create_general_properties_from_data(
                        row_data, pipeline_input, db
                    )
                    
                    successful_items.append({
                        "id": pipeline_input.id,
                        "name": pipeline_input.name,
                        "created_at": pipeline_input.created_at,
                        "properties": properties_list,
                    })
                    
            except Exception as e:
                failed_items.append({
                    "row": index + 2,  # +2 because index starts at 0 and we skip header
                    "variant_name": row.get("Variant Name", "Unknown"),
                    "error": str(e),
                })
                continue
        
        if successful_items:
            db.commit()
        
        return {
            "total": len(successful_items),
            "items": successful_items,
            "total_processed": len(df),
            "successful": len(successful_items),
            "failed": len(failed_items),
            "failed_items": failed_items,
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.get("/product/properties")
async def get_all_product_properties(db: Session = Depends(get_db)):
    """Get all products with their dynamic properties"""
    try:
        products = db.query(PipelineInput).filter(PipelineInput.is_usable == 1).all()
        
        items = []
        for product in products:
            properties = []
            
            # Get all properties for this product
            product_properties = (
                db.query(GeneralProperty)
                .filter(
                    GeneralProperty.referrer_id == product.id,
                    GeneralProperty.property_type == "pipeline_input",
                    GeneralProperty.is_usable == 1,
                )
                .all()
            )
            
            for prop in product_properties:
                properties.append({
                    "id": prop.id,
                    "property_label": prop.property_label,
                    "property_key": prop.property_key,
                    "property_value": prop.property_value,
                    "created_at": prop.created_at,
                })
            
            items.append({
                "id": product.id,
                "name": product.name,
                "created_at": product.created_at,
                "properties": properties,
            })
        
        return {"total": len(items), "items": items}
        
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching properties: {str(e)}"
        )


@router.put("/product/{product_id}")
async def update_product(
    product_id: int,
    data: Dict[str, Any],
    db: Session = Depends(get_db),
):
    """Update product with dynamic property handling"""
    try:
        db.begin()
        
        # 1. Get existing pipeline input
        pipeline_input = (
            db.query(PipelineInput)
            .filter(PipelineInput.id == product_id, PipelineInput.is_usable == 1)
            .first()
        )
        
        if not pipeline_input:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Update pipeline input name if changed
        variant_name = data.get("Variant Name", "").lower()
        if variant_name and pipeline_input.name != variant_name:
            pipeline_input.name = variant_name
            db.flush()
        
        # 2. Soft delete existing properties
        db.query(GeneralProperty).filter(
            GeneralProperty.referrer_id == product_id,
            GeneralProperty.property_type == "pipeline_input",
            GeneralProperty.is_usable == 1,
        ).update({"is_usable": 0})
        
        # 3. Create new properties from updated data
        properties_list = create_general_properties_from_data(data, pipeline_input, db)
        
        # Commit transaction
        db.commit()
        
        return {
            "id": pipeline_input.id,
            "name": pipeline_input.name,
            "created_at": pipeline_input.created_at,
            "properties": properties_list,
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/product/{product_id}")
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    """Soft delete product and its properties"""
    try:
        db.begin()
        
        # 1. Get pipeline input
        pipeline_input = (
            db.query(PipelineInput)
            .filter(PipelineInput.id == product_id, PipelineInput.is_usable == 1)
            .first()
        )
        
        if not pipeline_input:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # 2. Soft delete pipeline input and properties
        pipeline_input.is_usable = 0
        
        db.query(GeneralProperty).filter(
            GeneralProperty.referrer_id == product_id,
            GeneralProperty.property_type == "pipeline_input",
            GeneralProperty.is_usable == 1,
        ).update({"is_usable": 0})
        
        # Commit transaction
        db.commit()
        
        return {"message": "Product successfully deleted"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/product/column-mapping")
async def get_column_mapping():
    """Get the hardcoded column to property_key mapping"""
    return {
        "mapping": COLUMN_PROPERTY_MAPPING,
        "pipeline_input_fields": list(PIPELINE_INPUT_FIELDS),
        "description": "Column names mapped to property_key values. Unmapped columns get empty property_key."
    }
