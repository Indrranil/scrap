from pydantic import BaseModel
from typing import Optional

class ApplicationSessionBase(BaseModel):
   application_id: int
   name: str
   created_by: int
   ended_at: Optional[int] = None
   is_usable: int = 1

class ApplicationSessionResponse(ApplicationSessionBase):
   id: int
   created_at: int
   class Config:
       from_attributes = True