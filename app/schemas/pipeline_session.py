from pydantic import BaseModel
from typing import Optional

class PipelineSessionBase(BaseModel):
    pipeline_id: int
    pipeline_input_id: int
    name: Optional[str] = None
    created_by: int
    ended_at: Optional[int] = None
    is_usable: int

class PipelineSessionCreate(PipelineSessionBase):
    pass

class PipelineSession(PipelineSessionBase):
    id: int
    created_at: int
    class Config:
        from_attributes = True