from pydantic import BaseModel
from pydantic import Field, EmailStr
from typing import List, Optional

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    firstName: str = Field(..., min_length=2, max_length=50)
    lastName: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=8)
    roles: Optional[List[str]] = []

class UserResponse(BaseModel):
    username: str
    firstName: str
    lastName: str

class UsersListResponse(BaseModel):
    total: int
    users: List[UserResponse]