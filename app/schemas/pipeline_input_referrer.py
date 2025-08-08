from pydantic import BaseModel


class PipelineInputReferrerBase(BaseModel):
    key: str
    value: str
    pipeline_input_id: int
    is_usable: int = 1


class PipelineInputReferrerResponse(PipelineInputReferrerBase):
    id: int
    created_at: int

    class Config:
        from_attributes = True
