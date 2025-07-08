# schemas/pipeline_session.py
from fastapi import HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional

from starlette import status


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


class Pagination(BaseModel):
    page: Optional[int] = 1

    @field_validator('page')
    @classmethod
    def check_page(cls, p: int):
        if p < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='invalid page')
        return p


class Sort(BaseModel):
    sort: int = 0  # 0 = ascending, 1 = descending


class Limit(BaseModel):
    limit: int = -1  # -1 = no limit


class BasicFilter(Sort, Limit):
    last_index: Optional[int] = 0
