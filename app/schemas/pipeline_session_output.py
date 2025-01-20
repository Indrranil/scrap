from pydantic import BaseModel
from typing import Optional

class PipelineSessionOutputBase(BaseModel):
    pipeline_session_id: int
    name: Optional[str] = None
    ended_at: Optional[int] = None

class PipelineSessionOutputCreate(PipelineSessionOutputBase):
    pass

class PipelineSessionOutput(PipelineSessionOutputBase):
    id: int
    created_at: int
    is_usable: int

    class Config:
        from_attributes = True