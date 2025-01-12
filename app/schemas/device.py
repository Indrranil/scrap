# schemas/device.py
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class MachineType(str, Enum):
    camera = "camera"
    server = "server"
    rejector = "rejector"

DEVICE_TYPE_MAPPING = {
    "type 1": "camera",
    "type 2": "server",
    "type 3": "rejector"
}

class DeviceUploadCreate(BaseModel):
    machine_name: str = Field(..., alias="Device Name")
    ip_address: str = Field(..., alias="IP Address")
    mac_address: str = Field(..., alias="Mac Address")
    machine_type: str = Field(..., alias="Device Type")
    baud_rate: str = Field(..., alias="Baud Rate")
    starting_address: str = Field(..., alias="Starting Address")

    class Config:
        populate_by_name = True
        populate_by_alias = True
        alias_generator = str.title  # This will handle the case conversion

class DeviceResponse(BaseModel):
    id: int
    mid: str
    machine_name: str
    machine_type: MachineType
    created_at: int
    properties: dict

    class Config:
        from_attributes = True