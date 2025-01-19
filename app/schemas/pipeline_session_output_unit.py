from pydantic import BaseModel
from typing import Optional, Literal

OutputUnitStatus = Literal['idle', 'ready', 'analysing', 'success', 'error']
class PipelineSessionOutputUnitBase(BaseModel):
    pipeline_session_output_id: int
    property_reference_id: int
    name: Optional[str] = None
    output_key: str
    output_value: str
    status: OutputUnitStatus
    is_usable: int

class PipelineSessionOutputUnitCreate(PipelineSessionOutputUnitBase):
    pass

class PipelineSessionOutputUnit(PipelineSessionOutputUnitBase):
    id: int
    created_at : int
    class Config:
        from_attributes = True