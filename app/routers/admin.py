import json
import os
import time
from io import StringIO
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.general_property import GeneralProperty
from app.models.machine import Machine
from app.models.pipeline_input import PipelineInput

router = APIRouter(prefix="/v1/admin", tags=["admin"])


# Load configuration from JSON files
def load_json_config(filename: str) -> Dict[str, Any]:
    """Load configuration from JSON file"""
    # Get the app directory (parent of routers directory)
    app_dir = os.path.dirname(os.path.dirname(__file__))
    json_path = os.path.join(app_dir, "json", filename)
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail=f"Configuration file {filename} not found at {json_path}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"Invalid JSON in {filename}")


# Load mappings from JSON files
COLUMN_PROPERTY_MAPPING: Dict[str, Dict[str, str]] = load_json_config("column_property_mapping.json")

# Pipeline Input core fields that go directly to PipelineInput table
PIPELINE_INPUT_FIELDS: set[str] = {"Variant Name"}

# Machine core fields that go directly to Machine table
MACHINE_FIELDS: set[str] = {"Name", "Machine Type"}

# Load form configurations from JSON file
FORM_CONFIGURATIONS: Dict[str, Dict[str, Any]] = load_json_config("form_configurations.json")


def create_pipeline_input_from_data(data: Dict[str, Any], db: Session, allow_duplicates: bool = False) -> PipelineInput:
    """Create new PipelineInput from data with duplicate prevention"""
    variant_name = data.get("Variant Name", "").strip()

    if not variant_name:
        raise ValueError("Variant Name is required")

    # Normalize variant name for comparison (case-insensitive)
    variant_name_lower = variant_name.lower()

    # Check if pipeline input already exists
    existing_pipeline_input = (
        db.query(PipelineInput)
        .filter(
            PipelineInput.name == variant_name_lower,
            PipelineInput.is_usable == 1,
        )
        .first()
    )

    if existing_pipeline_input:
        if allow_duplicates:
            # Return existing pipeline input (legacy behavior)
            return existing_pipeline_input
        else:
            # Prevent duplicate - raise error
            raise ValueError(f"Product with variant name '{variant_name}' already exists")

    # Create new pipeline input
    pipeline_input = PipelineInput(
        name=variant_name_lower,
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
) -> List[Dict[str, Any]]:
    """Create GeneralProperty records from remaining data fields"""
    properties_list: List[Dict[str, Any]] = []
    timestamp = int(time.time())

    for column_name, column_value in data.items():
        # Skip pipeline input fields and empty values
        if column_name in PIPELINE_INPUT_FIELDS or column_value is None or column_value == "":
            continue

        # Get property_key from mapping, or empty string if not found
        mapping_entry = COLUMN_PROPERTY_MAPPING.get(column_name, {})
        if isinstance(mapping_entry, dict):
            property_key: str = mapping_entry.get("property_key", "")
            property_label: str = mapping_entry.get("property_label", "")
        else:
            # Handle legacy string entries (shouldn't happen now but for safety)
            property_key = str(mapping_entry)
            property_label = column_name

        # Create GeneralProperty record
        property_entity = GeneralProperty(
            referrer_id=pipeline_input.id,
            property_type="pipeline_input",
            property_key=property_key,
            property_label=property_label,
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

    # Automatically add "others" property type for Color and Perfume
    others_properties = [
        {"property_label": "Color: Matches with the standard?", "property_value": "1"},
        {"property_label": "Perfume: Matches with the standard?", "property_value": "1"}
    ]

    for others_prop in others_properties:
        property_entity = GeneralProperty(
            referrer_id=pipeline_input.id,
            property_type="pipeline_input",
            property_key="others",
            property_label=others_prop["property_label"],
            property_value=others_prop["property_value"],
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

    # Check if form_factor is Sachet and add perforation properties
    form_factor_value = data.get("Form Factor", "")
    if form_factor_value and form_factor_value.lower() == "sachet":
        perforation_properties = [
            {"property_label": "Min", "property_value": ""},
            {"property_label": "Max", "property_value": ""},
            {"property_label": "Avg", "property_value": ""},
            {"property_label": "Raw", "property_value": ""}
        ]

        for perf_prop in perforation_properties:
            property_entity = GeneralProperty(
                referrer_id=pipeline_input.id,
                property_type="pipeline_input",
                property_key="perforation",
                property_label=perf_prop["property_label"],
                property_value=perf_prop["property_value"],
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

    # Check if PQS Carton flag is set and add pqs_carton properties
    pqs_carton_value = data.get("PQS Carton", "")
    if pqs_carton_value == "1":
        pqs_property_columns = [
            "Front Face", "Back Face", "Top Face", "Bottom Face",
            "Left Face", "Right Face", "Damage", "Flap Open",
            "Grease/Dirt", "Color Mismatch"
        ]

        for column_name in pqs_property_columns:
            property_entity = GeneralProperty(
                referrer_id=pipeline_input.id,
                property_type="pipeline_input",
                property_key="pqs_carton",
                property_label=column_name,
                property_value="1" if column_name.lower().endswith("face") else "",
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

    # Check if PQS Tube flag is set and add pqs_tube properties
    pqs_tube_value = data.get("PQS Tube", "")
    if pqs_tube_value == "1":
        pqs_property_columns = [
            "Front Face", "Back Face", "Damage", "Misaligned Cap",
            "Grease/Dirt", "Color Mismatch", "Loose Cap", "Off Center"
        ]

        for column_name in pqs_property_columns:
            property_entity = GeneralProperty(
                referrer_id=pipeline_input.id,
                property_type="pipeline_input",
                property_key="pqs_tube",
                property_label=column_name,
                property_value="1" if column_name.lower().endswith("face") else "",
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


def create_machine_from_data(data: Dict[str, Any], db: Session) -> Machine:
    """Create or get existing Machine from data"""
    machine_name = data.get("Name", "").strip()
    machine_type = data.get("Machine Type", "").strip()

    if not machine_name:
        raise ValueError("Machine Name is required")
    if not machine_type:
        raise ValueError("Machine Type is required")

    # Check if machine already exists
    machine = (
        db.query(Machine)
        .filter(
            Machine.name == machine_name,
            Machine.machine_type == machine_type,
            Machine.is_usable == 1,
        )
        .first()
    )

    if not machine:
        machine = Machine(
            name=machine_name,
            machine_type=machine_type,
            created_at=int(time.time()),
            is_usable=1
        )
        db.add(machine)
        db.flush()

    return machine


def create_machine_properties_from_data(
    data: Dict[str, Any],
    machine: Machine,
    db: Session
) -> List[Dict[str, Any]]:
    """Create GeneralProperty records from machine data fields"""
    properties_list: List[Dict[str, Any]] = []
    timestamp = int(time.time())

    for column_name, column_value in data.items():
        # Skip machine fields, empty values, and unnamed columns
        if (
            column_name in MACHINE_FIELDS or
            column_value is None or
            column_value == "" or
            column_name.strip().lower().startswith("unnamed:")
        ):
            continue

        # Convert column name to property_key (lowercase with underscores)
        property_key = column_name.lower().replace(" ", "_").replace("-", "_")

        # Create GeneralProperty record
        property_entity = GeneralProperty(
            referrer_id=machine.id,
            property_type="machine",
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

    # Return name, type, and property_type for filtered fields
    simplified_fields = [{"name": field["name"], "type": field["type"], "property_type": field.get("property_type", ""), "options": field.get("options", "")} for field in fields]

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
        allow_duplicates: bool = False,
        db: Session = Depends(get_db),
):
    """Single product upload with dynamic property creation and duplicate prevention"""
    try:
        db.begin()

        # 1. Create Pipeline Input (with duplicate prevention)
        pipeline_input = create_pipeline_input_from_data(data, db, allow_duplicates=allow_duplicates)

        # 2. Create General Properties from remaining fields
        properties_list = create_general_properties_from_data(data, pipeline_input, db)

        # Commit transaction
        db.commit()

        return {
            "success": True,
            "message": "Product created successfully",
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

    except ValueError as e:
        db.rollback()
        # Handle duplicate/validation errors with 400 status
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/product/bulk")
async def create_bulk_product_upload(
        file: UploadFile = File(...),
        allow_duplicates: bool = False,
        db: Session = Depends(get_db),
):
    """Bulk product upload with dynamic property creation from CSV"""
    try:
        contents = await file.read()
        df = pd.read_csv(StringIO(contents.decode("utf-8")), dtype=str)

        # Handle unnamed columns by using first non-empty row as headers
        if all(col.startswith("Unnamed:") for col in df.columns):
            # Find the first non-empty row to use as headers
            header_row_index: int = 0
            for i, row in df.iterrows():
                if not all(pd.isna(val) or str(val).strip() == "" for val in row):
                    header_row_index = i  # type: ignore
                    break

            headers = df.iloc[header_row_index].tolist()
            # Skip empty rows and header row, start from data rows
            df = pd.read_csv(
                StringIO(contents.decode("utf-8")),
                skiprows=header_row_index + 1,
                names=headers,
                dtype=str
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

        successful_items: List[Dict[str, Any]] = []
        failed_items: List[Dict[str, Any]] = []

        for index, row in df.iterrows():
            try:
                with db.begin_nested():
                    # Convert row to dictionary, handling NaN values
                    row_data: Dict[str, Any] = {}
                    for col in df.columns:
                        value: Any = row[col]
                        if pd.notna(value) and value != "" and str(value).strip() != "":
                            # Handle potential float conversion issues
                            row_data[col] = str(value)

                    print(row_data)
                    # 1. Create Pipeline Input (with duplicate prevention)
                    pipeline_input = create_pipeline_input_from_data(row_data, db, allow_duplicates=allow_duplicates)

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
                    "row": index + 2,  # type: ignore  # +2 because index starts at 0 and we skip header
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


@router.post("/machine/bulk")
async def create_bulk_machine_upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Bulk machine upload with dynamic property creation from CSV"""
    try:
        contents = await file.read()
        df = pd.read_csv(StringIO(contents.decode("utf-8")))

        # Handle unnamed columns by using first non-empty row as headers
        if all(col.startswith("Unnamed:") for col in df.columns):
            # Find the first non-empty row to use as headers
            header_row_index: int = 0
            for i, row in df.iterrows():
                if not all(pd.isna(val) or str(val).strip() == "" for val in row):
                    header_row_index = i  # type: ignore
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
        required_columns = ["Name", "Machine Type"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_columns)}",
            )

        successful_items: List[Dict[str, Any]] = []
        failed_items: List[Dict[str, Any]] = []

        for index, row in df.iterrows():
            try:
                with db.begin_nested():
                    # Convert row to dictionary, handling NaN values
                    row_data: Dict[str, Any] = {}
                    for col in df.columns:
                        value: Any = row[col]
                        if pd.notna(value) and value != "" and str(value).strip() != "":
                            # Handle potential float conversion issues
                            if isinstance(value, float):
                                if not (value == float('inf') or value == float('-inf') or value != value):
                                    row_data[col] = value
                            else:
                                row_data[col] = value

                    # 1. Create/Get Machine
                    machine = create_machine_from_data(row_data, db)

                    # 2. Create General Properties from remaining fields
                    properties_list = create_machine_properties_from_data(
                        row_data, machine, db
                    )

                    successful_items.append({
                        "id": machine.id,
                        "name": machine.name,
                        "machine_type": machine.machine_type,
                        "created_at": machine.created_at,
                        "properties": properties_list,
                    })

            except Exception as e:
                failed_items.append({
                    "row": index + 2,  # type: ignore  # +2 because index starts at 0 and we skip header
                    "machine_name": row.get("Name", "Unknown"),
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


@router.post("/machine")
async def create_machine_upload(
    data: Dict[str, Any],
    db: Session = Depends(get_db),
):
    """Single machine upload with dynamic property creation"""
    try:
        db.begin()

        # 1. Create/Get Machine
        machine = create_machine_from_data(data, db)

        # 2. Create General Properties from remaining fields
        properties_list = create_machine_properties_from_data(data, machine, db)

        # Commit transaction
        db.commit()

        return {
            "total": 1,
            "items": [
                {
                    "id": machine.id,
                    "name": machine.name,
                    "machine_type": machine.machine_type,
                    "created_at": machine.created_at,
                    "properties": properties_list,
                }
            ],
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/machine/properties")
async def get_all_machine_properties(db: Session = Depends(get_db)):
    """Get all machines with their dynamic properties"""
    try:
        machines = db.query(Machine).filter(Machine.is_usable == 1).all()

        items: List[Dict[str, Any]] = []
        for machine in machines:
            properties: List[Dict[str, Any]] = []

            # Get all properties for this machine
            machine_properties = (
                db.query(GeneralProperty)
                .filter(
                    GeneralProperty.referrer_id == machine.id,
                    GeneralProperty.property_type == "machine",
                    GeneralProperty.is_usable == 1,
                )
                .all()
            )

            for prop in machine_properties:
                properties.append({
                    "id": prop.id,
                    "property_label": prop.property_label,
                    "property_key": prop.property_key,
                    "property_value": prop.property_value,
                    "created_at": prop.created_at,
                })

            items.append({
                "id": machine.id,
                "name": machine.name,
                "machine_type": machine.machine_type,
                "created_at": machine.created_at,
                "properties": properties,
            })

        return {"total": len(items), "items": items}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching machine properties: {str(e)}"
        )


@router.get("/product/properties")
async def get_all_product_properties(db: Session = Depends(get_db)):
    """Get all products with their dynamic properties"""
    try:
        products = db.query(PipelineInput).filter(PipelineInput.is_usable == 1).all()

        items: List[Dict[str, Any]] = []
        for product in products:
            properties: List[Dict[str, Any]] = []

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
        pipeline_input.is_usable = 0  # type: ignore

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
