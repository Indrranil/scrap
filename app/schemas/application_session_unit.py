from pydantic import BaseModel
from typing import Optional

class ApplicationSessionUnitBase(BaseModel):
    application_session_id: int
    name: str
    is_usable: int = 1
    ended_at: Optional[int] = None

class ApplicationSessionUnitResponse(ApplicationSessionUnitBase):
    id: int
    created_at: int

    class Config:
        from_attributes = True