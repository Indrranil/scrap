from pydantic import BaseModel

class PipelineBase(BaseModel):
   name: str
   is_usable: int = 1

class PipelineResponse(PipelineBase):
   id: int
   created_at: int
   
   class Config:
       from_attributes = True