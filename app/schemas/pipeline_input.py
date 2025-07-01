from pydantic import BaseModel


class PipelineInputBase(BaseModel):
    name: str
    is_usable: int = 1


class PipelineInputResponse(PipelineInputBase):
    id: int
    created_at: int

    class Config:
        from_attributes = True
