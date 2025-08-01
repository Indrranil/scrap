# schemas/device.py
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MachineType(str, Enum):
    weight_machine = "weight_machine"
    perforation = "perforation"
    rejector = "rejector"


class DeviceUploadCreate(BaseModel):
    name: str = Field(...)
    mac_address: str = Field(...)
    machine_type: str = Field(...)
    ip_address: Optional[str] = Field(None)
    baud_rate: Optional[str] = Field(None)
    starting_address: Optional[str] = Field(None)


class DeviceResponse(BaseModel):
    id: int
    mid: str
    name: str
    machine_type: MachineType
    created_at: int
    properties: dict

    class Config:
        from_attributes = True
