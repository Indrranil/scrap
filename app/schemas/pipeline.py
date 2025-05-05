from typing import Optional

from pydantic import BaseModel, Field


class PipelineBase(BaseModel):
    name: str
    is_running: Optional[int] = Field(default=0)
    application_id: int
    is_usable: int


class PipelineCreate(PipelineBase):
    pass


class Pipeline(PipelineBase):
    id: int
    created_at: int

    class Config:
        from_attributes = True
