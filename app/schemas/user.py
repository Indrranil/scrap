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
    id: str
    username: str
    firstName: Optional[str] = ''
    lastName: Optional[str] = ''
    email: Optional[str] = ''
    enabled: Optional[bool] = True

class UsersListResponse(BaseModel):
    total: int
    users: List[UserResponse]
    
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    password: Optional[str] = None
    roles: Optional[List[str]] = None