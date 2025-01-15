from fastapi import APIRouter, HTTPException, Depends,UploadFile, File
from schemas.product_upload import ProductUploadCreate
from sqlalchemy.orm import Session
from database.connection import get_db
import time
from fastapi.responses import JSONResponse
import pandas as pd
from io import StringIO
from typing import Dict, Any
from models.pipeline_input import PipelineInput
from models.pipeline_input_referrer import PipelineInputReferrer
from models.general_property import GeneralProperty

router = APIRouter(prefix="/v1/product", tags=["product"])

@router.post("/")
async def create_product_upload(
    data: ProductUploadCreate,
    db: Session = Depends(get_db),
):
    try:
        # Remove context manager and start transaction manually
        db.begin()

        # 1. Check/Create Pipeline Input for variant
        pipeline_input = db.query(PipelineInput).filter(
            PipelineInput.name == data.variant_name.lower(),
            PipelineInput.is_usable == 1
        ).first()

        if not pipeline_input:
            pipeline_input = PipelineInput(
                name=data.variant_name.lower(),
                created_at=int(time.time()),
                is_usable=1
            )
            db.add(pipeline_input)
            db.flush()

        # Store all properties for response
        properties_list = []
        timestamp = int(time.time())

        # 2. Create CLD Barcode Reference
        cld_referrer = PipelineInputReferrer(
            key="cld_barcode",
            value=data.cld_barcode.lower(),
            pipeline_input_id=pipeline_input.id,
            created_at=timestamp,
            is_usable=1
        )
        db.add(cld_referrer)
        db.flush()

        # Add CLD barcode to properties list
        properties_list.append({
            "id": cld_referrer.id,
            "property_label": "CLD Barcode",
            "property_key": "cld_barcode",
            "property_value": cld_referrer.value,
            "created_at": cld_referrer.created_at
        })

        # 3. Handle basic properties
        basic_properties = {
            "material": {
                "Front": data.material_code_front,
                "Back": data.material_code_back
            },
            "coding": {
                "Factory Code": data.factory_code,
                "Price": data.price,
                "USP": data.usp,
                "Manufacturing Date": data.manufacturing_date,
                "Expiry Date": data.expiry_date,
            },
            "specifications": {
                "target_weight": str(data.target_weight) if data.target_weight is not None else None,
                "tare_weight": str(data.tare_weight) if data.tare_weight is not None else None,
                "FORM FACTOR": data.form_factor
            },
            "identifiers": {
                "product_name": data.product_name,
                "variant_barcode": data.variant_barcode
            }
        }

        # Add basic properties
        for group_key, group_properties in basic_properties.items():
            for property_label, property_value in group_properties.items():
                if property_value is not None:
                    property_entity = GeneralProperty(
                        referrer_id=pipeline_input.id,
                        property_type="pipeline_input",
                        property_key=group_key,
                        property_label=property_label,
                        property_value=str(property_value),
                        created_at=timestamp,
                        is_usable=1
                    )
                    db.add(property_entity)
                    db.flush()
                    
                    properties_list.append({
                        "id": property_entity.id,
                        "property_label": property_entity.property_label,
                        "property_key": property_entity.property_key,
                        "property_value": property_entity.property_value,
                        "created_at": property_entity.created_at
                    })

        # 4. Handle PQS properties if form factor is norden
        if data.form_factor and data.form_factor.lower() == "norden":
            pqs_properties = {
                "front_face": str(data.front_face) if data.front_face is not None else "1",
                "back_face": str(data.back_face) if data.back_face is not None else "1",
                "left_face": str(data.left_face) if data.left_face is not None else "1",
                "right_face": str(data.right_face) if data.right_face is not None else "1",
                "top_face": str(data.top_face) if data.top_face is not None else "1",
                "bottom_face": str(data.bottom_face) if data.bottom_face is not None else "1",
                "damage": data.damage if data.damage is not None else "",
                "flap_open": data.flap_open if data.flap_open is not None else "",
                "grease_dirt": data.grease_dirt if data.grease_dirt is not None else "",
                "color_mismatch": data.color_mismatch if data.color_mismatch is not None else ""
            }

            # Add PQS properties
            for label, value in pqs_properties.items():
                if value is not None:
                    # Add PQS Carton properties
                    carton_entity = GeneralProperty(
                        referrer_id=pipeline_input.id,
                        property_type="pipeline_input",
                        property_key="pqs_carton",
                        property_label=label,
                        property_value=str(value),
                        created_at=timestamp,
                        is_usable=1
                    )
                    db.add(carton_entity)
                    db.flush()
                    
                    properties_list.append({
                        "id": carton_entity.id,
                        "property_label": carton_entity.property_label,
                        "property_key": carton_entity.property_key,
                        "property_value": carton_entity.property_value,
                        "created_at": carton_entity.created_at
                    })

                    # Add PQS Tube properties
                    tube_entity = GeneralProperty(
                        referrer_id=pipeline_input.id,
                        property_type="pipeline_input",
                        property_key="pqs_tube",
                        property_label=label,
                        property_value=str(value),
                        created_at=timestamp,
                        is_usable=0
                    )
                    db.add(tube_entity)
                    db.flush()

        # Commit the transaction
        db.commit()
        
        return {
            "total": 1,
            "items": [{
                "id": pipeline_input.id,
                "name": pipeline_input.name,
                "created_at": pipeline_input.created_at,
                "properties": properties_list
            }]
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
    
def map_csv_to_schema(row: pd.Series) -> Dict[str, Any]:
    """Map CSV row to schema fields, handling missing columns"""
    schema_mapping = {
        "Variant Name": row.get("Variant Name", ""),
        "CLD Barcode": row.get("CLD Barcode", ""),
        "Form Factor": row.get("Form Factor", ""),
        "Product Name": row.get("Product Name", ""),
        "Variant Barcode": row.get("Variant Barcode", ""),
        "Material Code-Front": str(row.get("Material Code-Front", "")),
        "Material Code-Back": str(row.get("Material Code-Back", "")),
        "Price": str(row.get("Price", "")),
        "USP": str(row.get("USP", "")),
        "Manufacturing Date": str(row.get("Manufacturing Date", "")),
        "Expiry Date": str(row.get("Expiry Date", "")),
        "Factory Code": str(row.get("Factory Code", "")),
        "Target Weight (g)": float(row["Target Weight (g)"]) if pd.notna(row.get("Target Weight (g)")) else None,
        "Tare Weight (g)": float(row["Tare Weight (g)"]) if pd.notna(row.get("Tare Weight (g)")) else None
    }
    return {k: v for k, v in schema_mapping.items() if v}

@router.post("/bulk")
async def create_bulk_product_upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        contents = await file.read()
        df = pd.read_csv(StringIO(contents.decode('utf-8')))
        
        # Print all column names for debugging
        print("Original CSV columns:", df.columns.tolist())
        
        # Create mapping for unnamed columns
        if all(col.startswith('Unnamed:') for col in df.columns):
            headers = df.iloc[0].tolist()
            df = pd.read_csv(
                StringIO(contents.decode('utf-8')),
                skiprows=1,
                names=headers
            )

        # Check required columns
        required_columns = ["Variant Name", "CLD Barcode"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )

        successful_items = []
        failed_items = []

        for index, row in df.iterrows():
            try:
                with db.begin_nested():
                    # Map row data to schema
                    mapped_data = map_csv_to_schema(row)
                    product_data = ProductUploadCreate(**mapped_data)
                    properties_list = []
                    timestamp = int(time.time())

                    # 1. Create/Get Pipeline Input
                    pipeline_input = db.query(PipelineInput).filter(
                        PipelineInput.name == product_data.variant_name.lower(),
                        PipelineInput.is_usable == 1
                    ).first()

                    if not pipeline_input:
                        pipeline_input = PipelineInput(
                            name=product_data.variant_name.lower(),
                            created_at=timestamp,
                            is_usable=1
                        )
                        db.add(pipeline_input)
                        db.flush()

                    # 2. Create CLD Barcode Reference
                    cld_referrer = PipelineInputReferrer(
                        key="cld_barcode",
                        value=product_data.cld_barcode.lower(),
                        pipeline_input_id=pipeline_input.id,
                        created_at=timestamp,
                        is_usable=1
                    )
                    db.add(cld_referrer)
                    db.flush()

                    properties_list.append({
                        "id": cld_referrer.id,
                        "property_label": "CLD Barcode",
                        "property_key": "cld_barcode",
                        "property_value": cld_referrer.value,
                        "created_at": cld_referrer.created_at
                    })

                    # 3. Add basic properties
                    basic_properties = {
                        "material": {
                            "Front": product_data.material_code_front,
                            "Back": product_data.material_code_back
                        },
                        "coding": {
                            "Factory Code": product_data.factory_code,
                            "Price": product_data.price,
                            "USP": product_data.usp,
                            "Manufacturing Date": product_data.manufacturing_date,
                            "Expiry Date": product_data.expiry_date,
                        },
                        "specifications": {
                            "target_weight": str(product_data.target_weight) if product_data.target_weight is not None else None,
                            "tare_weight": str(product_data.tare_weight) if product_data.tare_weight is not None else None,
                            "FORM FACTOR": product_data.form_factor
                        },
                        "identifiers": {
                            "product_name": product_data.product_name,
                            "variant_barcode": product_data.variant_barcode
                        }
                    }

                    for group_key, group_properties in basic_properties.items():
                        for property_label, property_value in group_properties.items():
                            if property_value is not None:
                                prop_entity = GeneralProperty(
                                    referrer_id=pipeline_input.id,
                                    property_type="pipeline_input",
                                    property_key=group_key,
                                    property_label=property_label,
                                    property_value=str(property_value),
                                    created_at=timestamp,
                                    is_usable=1
                                )
                                db.add(prop_entity)
                                db.flush()
                                
                                properties_list.append({
                                    "id": prop_entity.id,
                                    "property_label": property_label,
                                    "property_key": group_key,
                                    "property_value": str(property_value),
                                    "created_at": timestamp
                                })

                    # 4. Handle PQS properties
                    if product_data.form_factor and product_data.form_factor.lower() == "norden":
                        for is_tube in [False, True]:
                            property_key = "pqs_tube" if is_tube else "pqs_carton"
                            is_usable = 0 if is_tube else 1
                            
                            pqs_properties = {
                                "front_face": "1", "back_face": "1",
                                "left_face": "1", "right_face": "1",
                                "top_face": "1", "bottom_face": "1",
                                "damage": "", "flap_open": "",
                                "grease_dirt": "", "color_mismatch": ""
                            }

                            for label, value in pqs_properties.items():
                                pqs_entity = GeneralProperty(
                                    referrer_id=pipeline_input.id,
                                    property_type="pipeline_input",
                                    property_key=property_key,
                                    property_label=label,
                                    property_value=value,
                                    created_at=timestamp,
                                    is_usable=is_usable
                                )
                                db.add(pqs_entity)
                                db.flush()
                                
                                if is_usable == 1:  # Only add carton properties to response
                                    properties_list.append({
                                        "id": pqs_entity.id,
                                        "property_label": label,
                                        "property_key": property_key,
                                        "property_value": value,
                                        "created_at": timestamp
                                    })

                    successful_items.append({
                        "id": pipeline_input.id,
                        "name": pipeline_input.name,
                        "created_at": pipeline_input.created_at,
                        "properties": properties_list
                    })

            except Exception as e:
                failed_items.append({
                    "row": index + 2,
                    "variant_name": row.get("Variant Name", "Unknown"),
                    "error": str(e)
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
            "failed_items": failed_items
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )
        
        
@router.get("/properties")
async def get_all_product_properties(db: Session = Depends(get_db)):
    try:
        products = db.query(PipelineInput).filter(PipelineInput.is_usable == 1).all()
        
        items = []
        for product in products:
            properties = []
            
            # Get CLD barcode reference
            cld_referrer = db.query(PipelineInputReferrer).filter(
                PipelineInputReferrer.pipeline_input_id == product.id,
                PipelineInputReferrer.key == 'cld_barcode',
                PipelineInputReferrer.is_usable == 1
            ).first()
            
            if cld_referrer:
                properties.append({
                    "id": cld_referrer.id,
                    "property_label": "CLD Barcode",
                    "property_key": "cld_barcode",
                    "property_value": cld_referrer.value,
                    "created_at": cld_referrer.created_at
                })
            
            # Get other properties
            product_properties = db.query(GeneralProperty).filter(
                GeneralProperty.referrer_id == product.id,
                GeneralProperty.property_type == 'pipeline_input',
                GeneralProperty.is_usable == 1
            ).all()
            
            for prop in product_properties:
                properties.append({
                    "id": prop.id,
                    "property_label": prop.property_label,
                    "property_key": prop.property_key,
                    "property_value": prop.property_value,
                    "created_at": prop.created_at
                })
            
            items.append({
                "id": product.id,
                "name": product.name,
                "created_at": product.created_at,
                "properties": properties
            })

        return {
            "total": len(items),
            "items": items
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching properties: {str(e)}"
        )
        
@router.put("/{product_id}")
async def update_product(
    product_id: int,
    data: ProductUploadCreate,
    db: Session = Depends(get_db),
):
    try:
        # Start transaction
        db.begin()

        # 1. Get existing pipeline input
        pipeline_input = db.query(PipelineInput).filter(
            PipelineInput.id == product_id,
            PipelineInput.is_usable == 1
        ).first()

        if not pipeline_input:
            raise HTTPException(status_code=404, detail="Product not found")

        # Update pipeline input name if changed
        if pipeline_input.name != data.variant_name.lower():
            pipeline_input.name = data.variant_name.lower()
            db.flush()

        timestamp = int(time.time())
        properties_list = []

        # 2. Update CLD Barcode Reference
        cld_referrer = db.query(PipelineInputReferrer).filter(
            PipelineInputReferrer.pipeline_input_id == product_id,
            PipelineInputReferrer.key == "cld_barcode",
            PipelineInputReferrer.is_usable == 1
        ).first()

        if cld_referrer:
            cld_referrer.value = data.cld_barcode.lower()
            cld_referrer.created_at = timestamp
        else:
            cld_referrer = PipelineInputReferrer(
                key="cld_barcode",
                value=data.cld_barcode.lower(),
                pipeline_input_id=pipeline_input.id,
                created_at=timestamp,
                is_usable=1
            )
            db.add(cld_referrer)
        db.flush()

        properties_list.append({
            "id": cld_referrer.id,
            "property_label": "CLD Barcode",
            "property_key": "cld_barcode",
            "property_value": cld_referrer.value,
            "created_at": cld_referrer.created_at
        })

        # 3. Update basic properties
        basic_properties = {
            "material": {
                "Front": data.material_code_front,
                "Back": data.material_code_back
            },
            "coding": {
                "Factory Code": data.factory_code,
                "Price": data.price,
                "USP": data.usp,
                "Manufacturing Date": data.manufacturing_date,
                "Expiry Date": data.expiry_date,
            },
            "specifications": {
                "target_weight": str(data.target_weight) if data.target_weight is not None else None,
                "tare_weight": str(data.tare_weight) if data.tare_weight is not None else None,
                "FORM FACTOR": data.form_factor
            },
            "identifiers": {
                "product_name": data.product_name,
                "variant_barcode": data.variant_barcode
            }
        }

        # Set all existing properties as not usable
        db.query(GeneralProperty).filter(
            GeneralProperty.referrer_id == product_id,
            GeneralProperty.property_type == "pipeline_input",
            GeneralProperty.is_usable == 1
        ).update({"is_usable": 0})

        # Add updated properties
        for group_key, group_properties in basic_properties.items():
            for property_label, property_value in group_properties.items():
                if property_value is not None:
                    property_entity = GeneralProperty(
                        referrer_id=pipeline_input.id,
                        property_type="pipeline_input",
                        property_key=group_key,
                        property_label=property_label,
                        property_value=str(property_value),
                        created_at=timestamp,
                        is_usable=1
                    )
                    db.add(property_entity)
                    db.flush()
                    
                    properties_list.append({
                        "id": property_entity.id,
                        "property_label": property_entity.property_label,
                        "property_key": property_entity.property_key,
                        "property_value": property_entity.property_value,
                        "created_at": property_entity.created_at
                    })

        # 4. Handle PQS properties if form factor is norden
        if data.form_factor and data.form_factor.lower() == "norden":
            pqs_properties = {
                "front_face": str(data.front_face) if data.front_face is not None else "1",
                "back_face": str(data.back_face) if data.back_face is not None else "1",
                "left_face": str(data.left_face) if data.left_face is not None else "1",
                "right_face": str(data.right_face) if data.right_face is not None else "1",
                "top_face": str(data.top_face) if data.top_face is not None else "1",
                "bottom_face": str(data.bottom_face) if data.bottom_face is not None else "1",
                "damage": data.damage if data.damage is not None else "",
                "flap_open": data.flap_open if data.flap_open is not None else "",
                "grease_dirt": data.grease_dirt if data.grease_dirt is not None else "",
                "color_mismatch": data.color_mismatch if data.color_mismatch is not None else ""
            }

            for is_tube in [False, True]:
                property_key = "pqs_tube" if is_tube else "pqs_carton"
                is_usable = 0 if is_tube else 1

                for label, value in pqs_properties.items():
                    pqs_entity = GeneralProperty(
                        referrer_id=pipeline_input.id,
                        property_type="pipeline_input",
                        property_key=property_key,
                        property_label=label,
                        property_value=str(value),
                        created_at=timestamp,
                        is_usable=is_usable
                    )
                    db.add(pqs_entity)
                    db.flush()

                    if is_usable == 1:
                        properties_list.append({
                            "id": pqs_entity.id,
                            "property_label": label,
                            "property_key": property_key,
                            "property_value": str(value),
                            "created_at": timestamp
                        })

        # Commit the transaction
        db.commit()
        
        return {
            "id": pipeline_input.id,
            "name": pipeline_input.name,
            "created_at": pipeline_input.created_at,
            "properties": properties_list
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    try:
        # Start transaction
        db.begin()

        # 1. Get pipeline input
        pipeline_input = db.query(PipelineInput).filter(
            PipelineInput.id == product_id,
            PipelineInput.is_usable == 1
        ).first()

        if not pipeline_input:
            raise HTTPException(status_code=404, detail="Product not found")

        # 2. Soft delete pipeline input
        pipeline_input.is_usable = 0

        # 3. Soft delete all associated properties
        db.query(PipelineInputReferrer).filter(
            PipelineInputReferrer.pipeline_input_id == product_id,
            PipelineInputReferrer.is_usable == 1
        ).update({"is_usable": 0})

        db.query(GeneralProperty).filter(
            GeneralProperty.referrer_id == product_id,
            GeneralProperty.property_type == "pipeline_input",
            GeneralProperty.is_usable == 1
        ).update({"is_usable": 0})

        # Commit the transaction
        db.commit()

        return {"message": "Product successfully deleted"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))