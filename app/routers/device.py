from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
import pandas as pd
from io import StringIO
import time
from typing import Dict,List
from database.connection import get_db
from schemas.device import DeviceUploadCreate, DeviceResponse, DEVICE_TYPE_MAPPING
from models.machine import Machine
from models.general_property import GeneralProperty

router = APIRouter(prefix="/v1/device", tags=["device"])

def generate_mid(machine_name: str) -> str:
    """Generate standardized MID based on device name"""
    name_lower = machine_name.lower().replace(" ", "")
    
    if "weight" in name_lower:
        prefix = "wm"
    elif "perforation" in name_lower:
        prefix = "p"
    else:
        prefix = "d"
    
    suffix = str(int(time.time()))[-6:]
    return f"{prefix}_{suffix}"

def create_device_properties(
    db: Session,
    device_id: int,
    network_data: Dict[str, str],
    communication_data: Dict[str, str],
    timestamp: int
) -> Dict[str, str]:
    """Create device properties in general_property table"""
    properties_dict = {}
    
    # Network properties
    for property_label, property_value in network_data.items():
        if property_value and str(property_value).strip():
            property_entity = GeneralProperty(
                referrer_id=device_id,
                property_type="machine",
                property_key="network",
                property_label=property_label.lower(),
                property_value=str(property_value).lower(),
                created_at=timestamp,
                is_usable=1
            )
            db.add(property_entity)
            properties_dict[f"network_{property_label}"] = property_value

    # Communication properties
    for property_label, property_value in communication_data.items():
        if property_value and str(property_value).strip():
            property_entity = GeneralProperty(
                referrer_id=device_id,
                property_type="machine",
                property_key="communication",
                property_label=property_label.lower(),
                property_value=str(property_value).lower(),
                created_at=timestamp,
                is_usable=1
            )
            db.add(property_entity)
            properties_dict[f"communication_{property_label}"] = property_value

    return properties_dict

@router.post("/")
async def create_device(
    device: DeviceUploadCreate,
    db: Session = Depends(get_db),
):
    try:
        db.begin()

        mapped_type = DEVICE_TYPE_MAPPING.get(device.machine_type.lower())
        if not mapped_type:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid device type: {device.machine_type}. Must be one of: {', '.join(DEVICE_TYPE_MAPPING.keys())}"
            )

        # Store all properties for response
        properties_list = []
        timestamp = int(time.time())

        # Check if device exists
        existing_device = db.query(Machine).filter(
            Machine.machine_name == device.machine_name.lower(),
            Machine.is_usable == 1
        ).first()

        if existing_device:
            device_id = existing_device.id
            device_response = existing_device
        else:
            # Generate standardized MID and create new device
            generated_mid = generate_mid(device.machine_name)
            new_device = Machine(
                machine_name=device.machine_name.lower(),
                mid=generated_mid,
                machine_type=mapped_type,
                created_at=timestamp,
                is_usable=1
            )
            db.add(new_device)
            db.flush()
            device_id = new_device.id
            device_response = new_device
        
        # Add network properties
        network_properties = {
            "ip_address": device.ip_address,
            "mac_address": device.mac_address
        }
        
        for property_label, property_value in network_properties.items():
            if property_value and str(property_value).strip():
                network_entity = GeneralProperty(
                    referrer_id=device_id,
                    property_type="machine",
                    property_key="network",
                    property_label=property_label,
                    property_value=str(property_value).lower(),
                    created_at=timestamp,
                    is_usable=1
                )
                db.add(network_entity)
                db.flush()
                
                properties_list.append({
                    "id": network_entity.id,
                    "property_label": property_label,
                    "property_key": "network",
                    "property_value": str(property_value).lower(),
                    "created_at": timestamp
                })
        
        # Add communication properties
        communication_properties = {
            "baud_rate": device.baud_rate,
            "starting_address": device.starting_address
        }
        
        for property_label, property_value in communication_properties.items():
            if property_value and str(property_value).strip():
                comm_entity = GeneralProperty(
                    referrer_id=device_id,
                    property_type="machine",
                    property_key="communication",
                    property_label=property_label,
                    property_value=str(property_value).lower(),
                    created_at=timestamp,
                    is_usable=1
                )
                db.add(comm_entity)
                db.flush()
                
                properties_list.append({
                    "id": comm_entity.id,
                    "property_label": property_label,
                    "property_key": "communication",
                    "property_value": str(property_value).lower(),
                    "created_at": timestamp
                })
        
        # Add device type as a property
        device_type_entity = GeneralProperty(
            referrer_id=device_id,
            property_type="machine",
            property_key="specifications",
            property_label="device_type",
            property_value=mapped_type,
            created_at=timestamp,
            is_usable=1
        )
        db.add(device_type_entity)
        db.flush()
        
        properties_list.append({
            "id": device_type_entity.id,
            "property_label": "device_type",
            "property_key": "specifications",
            "property_value": mapped_type,
            "created_at": timestamp
        })

        db.commit()
        
        return {
            "total": 1,
            "items": [{
                "id": device_response.id,
                "name": device_response.machine_name,
                "created_at": device_response.created_at,
                "properties": properties_list
            }]
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating device: {str(e)}"
        )

@router.post("/bulk")
async def create_bulk_device_upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        contents = await file.read()
        df = pd.read_csv(StringIO(contents.decode('utf-8')))

        # Convert headers to lowercase for consistent handling
        df.columns = df.columns.str.lower()

        # Map headers to standard format
        header_mapping = {
            'ip address': 'ip_address',
            'mac address': 'mac_address',
            'device name': 'device_name',
            'device type': 'device_type',
            'baud rate': 'baud_rate',
            'starting address': 'starting_address'
        }
        df = df.rename(columns=header_mapping)

        # Check required columns
        required_columns = list(header_mapping.values())
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
                    device_data = DeviceUploadCreate(
                        machine_name=str(row["device_name"]).strip(),
                        ip_address=str(row["ip_address"]).strip(),
                        mac_address=str(row["mac_address"]).strip(),
                        machine_type=str(row["device_type"]).strip(),
                        baud_rate=str(row["baud_rate"]).strip(),
                        starting_address=str(row["starting_address"]).strip()
                    )

                    mapped_type = DEVICE_TYPE_MAPPING.get(device_data.machine_type.lower())
                    if not mapped_type:
                        raise ValueError(f"Invalid device type: {device_data.machine_type}")

                    properties_list = []
                    timestamp = int(time.time())

                    # Create or get existing device
                    existing_device = db.query(Machine).filter(
                        Machine.machine_name == device_data.machine_name.lower(),
                        Machine.is_usable == 1
                    ).first()

                    if existing_device:
                        device = existing_device
                    else:
                        generated_mid = generate_mid(device_data.machine_name)
                        device = Machine(
                            machine_name=device_data.machine_name.lower(),
                            mid=generated_mid,
                            machine_type=mapped_type,
                            created_at=timestamp,
                            is_usable=1
                        )
                        db.add(device)
                        db.flush()

                    # Add network properties
                    network_properties = {
                        "ip_address": device_data.ip_address,
                        "mac_address": device_data.mac_address
                    }

                    for label, value in network_properties.items():
                        if value and str(value).strip():
                            network_entity = GeneralProperty(
                                referrer_id=device.id,
                                property_type="machine",
                                property_key="network",
                                property_label=label,
                                property_value=str(value).lower(),
                                created_at=timestamp,
                                is_usable=1
                            )
                            db.add(network_entity)
                            db.flush()

                            properties_list.append({
                                "id": network_entity.id,
                                "property_label": label,
                                "property_key": "network",
                                "property_value": str(value).lower(),
                                "created_at": timestamp
                            })

                    # Add communication properties
                    communication_properties = {
                        "baud_rate": device_data.baud_rate,
                        "starting_address": device_data.starting_address
                    }

                    for label, value in communication_properties.items():
                        if value and str(value).strip():
                            comm_entity = GeneralProperty(
                                referrer_id=device.id,
                                property_type="machine",
                                property_key="communication",
                                property_label=label,
                                property_value=str(value).lower(),
                                created_at=timestamp,
                                is_usable=1
                            )
                            db.add(comm_entity)
                            db.flush()

                            properties_list.append({
                                "id": comm_entity.id,
                                "property_label": label,
                                "property_key": "communication",
                                "property_value": str(value).lower(),
                                "created_at": timestamp
                            })

                    # Add device type property
                    device_type_entity = GeneralProperty(
                        referrer_id=device.id,
                        property_type="machine",
                        property_key="specifications",
                        property_label="device_type",
                        property_value=mapped_type,
                        created_at=timestamp,
                        is_usable=1
                    )
                    db.add(device_type_entity)
                    db.flush()

                    properties_list.append({
                        "id": device_type_entity.id,
                        "property_label": "device_type",
                        "property_key": "specifications",
                        "property_value": mapped_type,
                        "created_at": timestamp
                    })

                    successful_items.append({
                        "id": device.id,
                        "name": device.machine_name,
                        "created_at": device.created_at,
                        "properties": properties_list
                    })

            except Exception as e:
                failed_items.append({
                    "row": index + 2,
                    "machine_name": row.get("device_name", "Unknown"),
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
            "failed_items": failed_items,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )
        


@router.get("/")
async def get_all_devices(db: Session = Depends(get_db)):
    try:
        devices = db.query(Machine).filter(Machine.is_usable == 1).all()
        
        items = []
        for device in devices:
            properties = []
            
            # Get all properties for this device
            device_properties = db.query(GeneralProperty).filter(
                GeneralProperty.referrer_id == device.id,
                GeneralProperty.property_type == 'machine',
                GeneralProperty.is_usable == 1
            ).all()
            
            # Convert properties to the new format
            for prop in device_properties:
                properties.append({
                    "id": prop.id,
                    "property_label": prop.property_label,
                    "property_key": prop.property_key,
                    "property_value": prop.property_value,
                    "created_at": prop.created_at
                })
            
            items.append({
                "id": device.id,
                "name": device.machine_name,
                "created_at": device.created_at,
                "properties": properties
            })

        return {
            "total": len(items),
            "items": items
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching devices: {str(e)}"
        )