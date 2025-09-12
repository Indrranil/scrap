import time
from io import StringIO
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.general_property import GeneralProperty
from app.models.machine import Machine
from app.models.pipeline_input import PipelineInput

router = APIRouter(prefix="/v1/admin", tags=["admin"])

# Hardcoded mapping for column_name to property_key
COLUMN_PROPERTY_MAPPING: Dict[str, Union[str, Dict[str, str]]] = {
    "Machine Code-Front": {"property_key": "front", "property_label": "Front"},
    "Machine Code-Back": {"property_key": "back", "property_label": "Back"},
    "Material Code-Front": {"property_key": "material_code", "property_label": "Front"},
    "Material Code-Back": {"property_key": "material_code", "property_label": "Back"},
    "Primary Carton Material Code": {"property_key": "primary_carton_material_code",
                                     "property_label": "Primary Carton Material Code"},
    "Secondary Carton Material Code": {"property_key": "secondary_carton_material_code",
                                       "property_label": "Secondary Carton Material Code"},
    "Tube Material Code": {"property_key": "tube_material_code", "property_label": "Tube Material Code"},
    "Factory Code": {"property_key": "coding", "property_label": "Factory Code"},
    "Carton Factory Code": {"property_key": "carton_coding", "property_label": "Factory Code"},
    "Tube Factory Code": {"property_key": "tube_coding", "property_label": "Factory Code"},
    "Price": {"property_key": "coding", "property_label": "Price"},
    "Carton Price": {"property_key": "carton_coding", "property_label": "Price"},
    "Tube Price": {"property_key": "tube_coding", "property_label": "Price"},
    "USP": {"property_key": "coding", "property_label": "USP"},
    "Carton USP": {"property_key": "carton_coding", "property_label": "USP"},
    "Tube USP": {"property_key": "tube_coding", "property_label": "USP"},
    "Manufacturing Date": {"property_key": "coding", "property_label": "Manufacturing Date"},
    "Carton Manufacturing Date": {"property_key": "carton_coding", "property_label": "Manufacturing Date"},
    "Tube Manufacturing Date": {"property_key": "tube_coding", "property_label": "Manufacturing Date"},
    "Expiry Date": {"property_key": "coding", "property_label": "Expiry Date"},
    "Target Weight (g)": {"property_key": "target_weight", "property_label": "Weight"},
    "Tare Weight (g)": {"property_key": "target_weight", "property_label": "Weight"},
    "Form Factor": {"property_key": "form_factor", "property_label": "Form Factor"},
    "Product Name": {"property_key": "product_name", "property_label": "Product Name"},
    "Variant Barcode": {"property_key": "variant_barcode", "property_label": "Barcode"},
    "CLD Barcode": {"property_key": "cld_barcode", "property_label": "CLD Barcode"},
    "Front Face": {"property_key": "front_face", "property_label": "Front Face"},
    "Back Face": {"property_key": "back_face", "property_label": "Back Face"},
    "Left Face": {"property_key": "left_face", "property_label": "Left Face"},
    "Right Face": {"property_key": "right_face", "property_label": "Right Face"},
    "Top Face": {"property_key": "top_face", "property_label": "Top Face"},
    "Bottom Face": {"property_key": "bottom_face", "property_label": "Bottom Face"},
    "Damage": {"property_key": "damage", "property_label": "Damage"},
    "Flap Open": {"property_key": "flap_open", "property_label": "Flap Open"},
    "Grease Dirt": {"property_key": "grease_dirt", "property_label": "Grease Dirt"},
    "Color Mismatch": {"property_key": "color_mismatch", "property_label": "Color Mismatch"}
}

# Pipeline Input core fields that go directly to PipelineInput table
PIPELINE_INPUT_FIELDS: set[str] = {"Variant Name"}

# Machine core fields that go directly to Machine table
MACHINE_FIELDS: set[str] = {"Name", "Machine Type"}

# Form field configurations for different form types
FORM_CONFIGURATIONS: Dict[str, Dict[str, Any]] = {
    "users": {
        "name": "User Management Form",
        "description": "Form for creating/editing users",
        "fields": [
            {
                "name": "username",
                "type": "text",
                "required": True,
                "property_type": "user_name"
            },
            {
                "name": "firstName",
                "type": "text",
                "required": True,
                "property_type": "first_name"
            },
            {
                "name": "lastName",
                "type": "text",
                "required": True,
                "property_type": "last_name"
            },
            {
                "name": "email",
                "type": "email",
                "required": False,
                "property_type": "email_address"
            },
            {
                "name": "Role",
                "type": "select",
                "options": ["admin", "user"],
                "required": False,
                "property_type": "role"
            },
            {
                "name": "Designation",
                "type": "select",
                "options": ["LQC", "SHIFT EXECUTIVE", "QUALITY EXECUTIVE"],
                "required": False,
                "property_type": "designation"
            }
        ]
    },
    "machines": {
        "name": "Machine Configuration Form",
        "description": "Form for setting up machines",
        "fields": [
            {
                "name": "Name",
                "type": "text",
                "required": True,
                "property_type": "name"
            },
            {
                "name": "IP Address",
                "type": "text",
                "required": True,
                "property_type": "ip_address"
            },
            {
                "name": "MAC Address",
                "type": "text",
                "required": True,
                "property_type": "mac_address"
            },
            {
                "name": "Machine Type",
                "type": "text",
                "required": True,
                "property_type": "machine_type"
            },
            {
                "name": "Baud Rate",
                "type": "number",
                "required": True,
                "property_type": "baud_rate"
            },
            {
                "name": "Starting Address",
                "type": "text",
                "required": True,
                "property_type": "starting_address"
            },
            {
                "name": "Unit Name",
                "type": "text",
                "required": False,
                "property_type": "unit_name"
            },
            {
                "name": "Factory Name",
                "type": "text",
                "required": False,
                "property_type": "factory_name"
            }
        ]
    },
    "product-carton": {
        "name": "Carton Product Form",
        "description": "Form for creating/editing carton products",
        "fields": [
            {
                "name": "CLD Barcode",
                "type": "text",
                "required": True,
                "property_type": "cld_barcode"
            },
            {
                "name": "Product Type",
                "type": "text",
                "required": True,
                "property_type": "product_type"
            },
            {
                "name": "Variant Name",
                "type": "text",
                "required": True,
                "property_type": "product_info"
            },
            {
                "name": "Barcode",
                "type": "text",
                "required": True,
                "property_type": "carton_coding"
            },
            {
                "name": "Factory Code",
                "type": "text",
                "required": False,
                "property_type": "carton_coding"
            },
            {
                "name": "Price",
                "type": "text",
                "required": False,
                "property_type": "carton_coding"
            },
            {
                "name": "USP",
                "type": "text",
                "required": False,
                "property_type": "carton_coding"
            },
            {
                "name": "Manufacturing Date",
                "type": "text",
                "required": False,
                "property_type": "carton_coding"
            },
            {
                "name": "Factory Code Tube",
                "type": "text",
                "required": False,
                "property_type": "tube_coding"
            },
            {
                "name": "Manufacturing Date Tube",
                "type": "text",
                "required": False,
                "property_type": "tube_coding"
            },
            {
                "name": "Batch Code Tube",
                "type": "text",
                "required": False,
                "property_type": "tube_coding"
            },
            {
                "name": "Primary Carton Material Code",
                "type": "text",
                "required": False,
                "property_type": "primary_carton_material_code"
            },
            {
                "name": "Tube Material Code",
                "type": "text",
                "required": False,
                "property_type": "tube_material_code"
            },
            {
                "name": "Target Weight",
                "type": "float",
                "required": False,
                "property_type": "target_weight"
            }
        ]
    },
    "product-sachet": {
        "name": "Sachet Product Form",
        "description": "Form for creating/editing sachet products",
        "fields": [
            {
                "name": "CLD Barcode",
                "type": "text",
                "required": True,
                "property_type": "sachet_coding"
            },
            {
                "name": "Variant Name",
                "type": "text",
                "required": True,
                "property_type": "product_info"
            },
            {
                "name": "Variant Barcode",
                "type": "text",
                "required": True,
                "property_type": "sachet_coding"
            },
            {
                "name": "Target Weight",
                "type": "float",
                "required": False,
                "property_type": "physical_properties"
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
    simplified_fields = [{"name": field["name"], "type": field["type"], "property_type": field.get("property_type", "")} for field in fields]

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
