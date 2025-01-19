from pydantic import BaseModel

class ApplicationBase(BaseModel):
    name: str
    is_usable: int

class ApplicationCreate(ApplicationBase):
    pass

class Application(ApplicationBase):
   id: int
   created_at: int
   class Config:
       from_attributes = True