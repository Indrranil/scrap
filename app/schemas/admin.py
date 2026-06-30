from typing import Optional

from pydantic import BaseModel, Field


class AdminProfileResponse(BaseModel):
    username: str
    name: str

    class Config:
        from_attributes = True


class AdminProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    old_password: Optional[str] = None
    new_password: Optional[str] = Field(None, min_length=1)
