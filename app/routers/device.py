import time
from io import StringIO
from typing import Dict, List, Union

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session
from starlette import status

from app.database.connection import get_db
from app.models.general_property import GeneralProperty
from app.models.machine import Machine
from app.schemas.device import DeviceUploadCreate

router = APIRouter(prefix="/v1/device", tags=["device"])


def generate_mid(name: str) -> str:
    """Generate standardized MID based on device name"""
    name_lower = name.lower().replace(" ", "")

    if "weight" in name_lower:
        prefix = "W"
    elif "perforation" in name_lower:
        prefix = "P"
    else:
        prefix = "R"

    suffix = str(int(time.time()))[-6:]
    return f"{prefix}_{suffix}"


@router.post("/")
async def create_device(
    device: DeviceUploadCreate,
    db: Session = Depends(get_db),
):
    try:
        db.begin()

        # Store all properties for response
        properties_list: List[Dict[str, Union[str, int]]] = []
        timestamp = int(time.time())

        # Check if device exists
        existing_device = (
            db.query(Machine)
            .filter(Machine.name == device.name, Machine.is_usable == 1)
            .first()
        )

        if existing_device:
            device_response = existing_device
        else:
            # Generate standardized MID and create new device
            generated_mid = generate_mid(device.name)
            new_device = Machine(
                name=device.name,
                mid=generated_mid,
                machine_type=device.machine_type,
                created_at=timestamp,
                is_usable=1,
            )
            db.add(new_device)
            db.flush()
            device_response = new_device

        db.commit()

        return {
            "total": 1,
            "items": [
                {
                    "id": device_response.id,
                    "name": device_response.name,
                    "created_at": device_response.created_at,
                    "properties": properties_list,
                }
            ],
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating device: {str(e)}")


@router.post("/bulk")
async def create_bulk_device_upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        contents = await file.read()
        df = pd.read_csv(StringIO(contents.decode("utf-8")))

        # Convert headers to lowercase for consistent handling
        df.columns = df.columns.str.lower()

        # Map headers to standard format
        header_mapping = {
            "ip address": "ip_address",
            "mac address": "mac_address",
            "device name": "device_name",
            "device type": "device_type",
            "baud rate": "baud_rate",
            "starting address": "starting_address",
        }
        df = df.rename(columns=header_mapping)

        # Check required columns
        required_columns = list(header_mapping.values())
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
                    device_data = DeviceUploadCreate(
                        name=str(row["device_name"]).strip(),
                        ip_address=str(row["ip_address"]).strip(),
                        mac_address=str(row["mac_address"]).strip(),
                        machine_type=str(row["device_type"]).strip(),
                        baud_rate=str(row["baud_rate"]).strip(),
                        starting_address=str(row["starting_address"]).strip(),
                    )

                    properties_list = []
                    timestamp = int(time.time())

                    # Create or get existing device
                    existing_device = (
                        db.query(Machine)
                        .filter(
                            Machine.name == device_data.name.lower(),
                            Machine.is_usable == 1,
                        )
                        .first()
                    )

                    if existing_device:
                        device = existing_device
                    else:
                        generated_mid = generate_mid(device_data.name)
                        device = Machine(
                            name=device_data.name.lower(),
                            mid=generated_mid,
                            machine_type=device.machine_type,
                            created_at=timestamp,
                            is_usable=1,
                        )
                        db.add(device)
                        db.flush()

                    # Add network properties
                    network_properties = {
                        "ip_address": device_data.ip_address,
                        "mac_address": device_data.mac_address,
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
                                is_usable=1,
                            )
                            db.add(network_entity)
                            db.flush()

                            properties_list.append(
                                {
                                    "id": network_entity.id,
                                    "property_label": label,
                                    "property_key": "network",
                                    "property_value": str(value).lower(),
                                    "created_at": timestamp,
                                }
                            )

                    # Add communication properties
                    communication_properties = {
                        "baud_rate": device_data.baud_rate,
                        "starting_address": device_data.starting_address,
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
                                is_usable=1,
                            )
                            db.add(comm_entity)
                            db.flush()

                            properties_list.append(
                                {
                                    "id": comm_entity.id,
                                    "property_label": label,
                                    "property_key": "communication",
                                    "property_value": str(value).lower(),
                                    "created_at": timestamp,
                                }
                            )

                    successful_items.append(
                        {
                            "id": device.id,
                            "name": device.name,
                            "created_at": device.created_at,
                            "properties": properties_list,
                        }
                    )

            except Exception as e:
                failed_items.append(
                    {
                        "row": index + 2,  # type: ignore
                        "name": row.get("name", "Unknown"),
                        "error": str(e),
                    }
                )
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


@router.get("/all")
async def get_all_devices(
    machine_type: str = Query(default="%"), db: Session = Depends(get_db)
):
    try:
        devices = (
            db.query(Machine)
            .filter(Machine.is_usable == 1, Machine.machine_type.like(machine_type))
            .all()
        )

        items = []
        for device in devices:
            properties = []

            # Get all properties for this device
            device_properties = (
                db.query(GeneralProperty)
                .filter(
                    GeneralProperty.referrer_id == device.id,
                    GeneralProperty.property_type == "machine",
                    GeneralProperty.is_usable == 1,
                )
                .all()
            )

            # Convert properties to the new format
            for prop in device_properties:
                properties.append(
                    {
                        "id": prop.id,
                        "property_label": prop.property_label,
                        "property_key": prop.property_key,
                        "property_value": prop.property_value,
                        "created_at": prop.created_at,
                    }
                )

            items.append(
                {
                    "id": device.id,
                    "name": device.name,
                    "created_at": device.created_at,
                    "machine_type": device.machine_type,
                    "properties": properties,
                }
            )

        return {"total": len(items), "items": items}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching devices: {str(e)}")


@router.get("/{machine_id}")
async def get_device(machine_id: str, db: Session = Depends(get_db)):
    device = (
        db.query(Machine)
        .filter(Machine.is_usable == 1, Machine.id == machine_id)
        .first()
    )

    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Machine not found"
        )

    properties = []

    # Get all properties for this device
    device_properties = (
        db.query(GeneralProperty)
        .filter(
            GeneralProperty.referrer_id == device.id,
            GeneralProperty.property_type == "machine",
            GeneralProperty.is_usable == 1,
        )
        .all()
    )

    # Convert properties to the new format
    for prop in device_properties:
        properties.append(
            {
                "id": prop.id,
                "property_label": prop.property_label,
                "property_key": prop.property_key,
                "property_value": prop.property_value,
                "created_at": prop.created_at,
            }
        )

    return {
        "id": device.id,
        "name": device.name,
        "created_at": device.created_at,
        "properties": properties,
    }


@router.put("/{device_id}")
async def update_device(
    device_id: int, device: DeviceUploadCreate, db: Session = Depends(get_db)
):
    try:
        # Start transaction
        db.begin()

        # Get existing device
        existing_device = (
            db.query(Machine)
            .filter(Machine.id == device_id, Machine.is_usable == 1)
            .first()
        )

        if not existing_device:
            raise HTTPException(
                status_code=404, detail=f"Device with ID {device_id} not found"
            )

        timestamp = int(time.time())
        properties_list = []

        # Update device details
        existing_device.name = device.name.lower()  # type: ignore
        existing_device.machine_type = device.machine_type  # type: ignore
        db.flush()

        # Set all existing properties as not usable
        db.query(GeneralProperty).filter(
            GeneralProperty.referrer_id == device_id,
            GeneralProperty.property_type == "machine",
            GeneralProperty.is_usable == 1,
        ).update({"is_usable": 0})

        # Add network properties
        network_properties = {
            "ip_address": device.ip_address,
            "mac_address": device.mac_address,
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
                    is_usable=1,
                )
                db.add(network_entity)
                db.flush()

                properties_list.append(
                    {
                        "id": network_entity.id,
                        "property_label": property_label,
                        "property_key": "network",
                        "property_value": str(property_value).lower(),
                        "created_at": timestamp,
                    }
                )

        # Add communication properties
        communication_properties = {
            "baud_rate": device.baud_rate,
            "starting_address": device.starting_address,
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
                    is_usable=1,
                )
                db.add(comm_entity)
                db.flush()

                properties_list.append(
                    {
                        "id": comm_entity.id,
                        "property_label": property_label,
                        "property_key": "communication",
                        "property_value": str(property_value).lower(),
                        "created_at": timestamp,
                    }
                )

        device_type_entity = GeneralProperty(
            referrer_id=device_id,
            property_type="machine",
            property_key="specifications",
            property_label="device_type",
            property_value=device.machine_type,
            created_at=timestamp,
            is_usable=1,
        )
        db.add(device_type_entity)
        db.flush()

        properties_list.append(
            {
                "id": device_type_entity.id,
                "property_label": "device_type",
                "property_key": "specifications",
                "property_value": device.machine_type,
                "created_at": timestamp,
            }
        )

        db.commit()

        return {
            "id": existing_device.id,
            "name": existing_device.name,
            "created_at": existing_device.created_at,
            "properties": properties_list,
        }

    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating device: {str(e)}")


@router.delete("/{device_id}")
async def delete_device(device_id: int, db: Session = Depends(get_db)):
    try:
        # Start transaction
        db.begin()

        # Get existing device
        device = (
            db.query(Machine)
            .filter(Machine.id == device_id, Machine.is_usable == 1)
            .first()
        )

        if not device:
            raise HTTPException(
                status_code=404, detail=f"Device with ID {device_id} not found"
            )

        # Soft delete the device
        device.is_usable = 0  # type: ignore

        # Soft delete all associated properties
        db.query(GeneralProperty).filter(
            GeneralProperty.referrer_id == device_id,
            GeneralProperty.property_type == "machine",
            GeneralProperty.is_usable == 1,
        ).update({"is_usable": 0})

        db.commit()

        return {
            "message": f"Device with ID {device_id} successfully deleted",
            "name": device.name,
        }

    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting device: {str(e)}")
