# schemas/device.py
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class MachineType(str, Enum):
    weight_machine = "weight_machine"
    perforation = "perforation"
    rejector = "rejector"


class DeviceUploadCreate(BaseModel):
    name: str = Field(...)
    mac_address: str = Field(...)
    machine_type: str = Field(...)


class DeviceResponse(BaseModel):
    id: int
    mid: str
    name: str
    machine_type: MachineType
    created_at: int
    properties: dict

    class Config:
        from_attributes = True
