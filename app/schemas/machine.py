from pydantic import BaseModel
from enum import Enum
from typing import Optional

class MachineType(str, Enum):
    camera = "camera"
    server = "server"
    rejector = "rejector"

class MachineBase(BaseModel):
    mid: str
    machine_name: str
    machine_type: MachineType
    is_usable: int = 1


class MachineResponse(MachineBase):
    id: int
    created_at: int

    class Config:
        from_attributes = True