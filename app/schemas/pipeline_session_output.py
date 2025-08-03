from typing import Optional

from pydantic import BaseModel

from app.schemas.pipeline_session_output_unit import PipelineSessionOutputUnitBase


class PipelineSessionOutputBase(BaseModel):
    pipeline_session_id: int
    name: Optional[str] = None
    ended_at: Optional[int] = None


class PipelineSessionOutputCreate(PipelineSessionOutputBase):
    pipeline_session_output_unit: Optional[PipelineSessionOutputUnitBase] = None


class PipelineSessionOutput(PipelineSessionOutputBase):
    id: int
    created_at: int
    is_usable: int

    class Config:
        from_attributes = True
