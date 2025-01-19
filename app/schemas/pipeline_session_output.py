from pydantic import BaseModel
from typing import Optional


class PipelineSessionOutputBase(BaseModel):
    pipeline_session_id: int
    name: Optional[str] = None
    created_at: int
    ended_at: Optional[int] = None
    is_usable: int

class PipelineSessionOutputCreate(PipelineSessionOutputBase):
    pass

class PipelineSessionOutput(PipelineSessionOutputBase):
    id: int
    created_at: int
    class Config:
        from_attributes = True