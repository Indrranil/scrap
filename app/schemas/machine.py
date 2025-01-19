from pydantic import BaseModel
from enum import Enum
from typing import Optional

class MachineType(str, Enum):
    weight_machine = "weight machine"
    perforation = "perforation"
    rejector = "rejector"

class MachineBase(BaseModel):
    mid: str
    name: str
    machine_type: MachineType
    is_usable: int = 1


class MachineResponse(MachineBase):
    id: int
    created_at: int

    class Config:
        from_attributes = True