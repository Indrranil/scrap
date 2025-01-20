# schemas/pipeline_session_output_unit.py
from pydantic import BaseModel
from typing import Optional
from enum import Enum

class UnitStatus(str, Enum):
    IDLE = 'idle'
    READY = 'ready'
    ANALYSING = 'analysing'
    SUCCESS = 'success'
    ERROR = 'error'

class PipelineSessionOutputUnitBase(BaseModel):
    pipeline_session_output_id: int
    property_reference_id: int
    name: Optional[str] = None
    output_key: str
    output_value: str
    status: Optional[UnitStatus] = UnitStatus.SUCCESS

class PipelineSessionOutputUnitCreate(PipelineSessionOutputUnitBase):
    pass

class PipelineSessionOutputUnitUpdate(BaseModel):
    property_reference_id: Optional[int] = None
    name: Optional[str] = None
    output_key: Optional[str] = None
    output_value: Optional[str] = None
    status: Optional[UnitStatus] = None

class PipelineSessionOutputUnit(PipelineSessionOutputUnitBase):
    id: int
    created_at: int
    is_usable: int

    class Config:
        from_attributes = True