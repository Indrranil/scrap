from pydantic import BaseModel

class ApplicationBase(BaseModel):
   name: str
   is_running: int
   pipeline_id: int
   is_usable: int = 1

class ApplicationResponse(ApplicationBase):
   id: int
   created_at: int
   class Config:
       from_attributes = True