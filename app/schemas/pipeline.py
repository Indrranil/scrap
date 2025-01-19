from pydantic import BaseModel

class PipelineBase(BaseModel):
    name: str
    is_running: int
    application_id: int
    is_usable: int

class PipelineCreate(PipelineBase):
    pass

class Pipeline(PipelineBase):
   id: int
   created_at: int
   
   class Config:
       from_attributes = True