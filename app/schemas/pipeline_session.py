# schemas/pipeline_session.py
from pydantic import BaseModel
from typing import Optional


class PipelineSessionBase(BaseModel):
    pipeline_id: int  # Changed from application_id
    pipeline_input_id: Optional[int] = None
    name: Optional[str] = None
    created_by: Optional[str] = None
    ended_at: Optional[int] = None


class PipelineSessionCreate(PipelineSessionBase):
    pass


class PipelineSession(PipelineSessionBase):
    id: int
    created_at: int
    is_usable: int

    class Config:
        from_attributes = True
