from typing import List, Optional

from pydantic import BaseModel


class LoginRequest(BaseModel):
    login_id: str
    password: str


class EmployeeSummary(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    plant_id: Optional[int] = None
    plant_name: Optional[str] = None
    scrapeyard_id: Optional[int] = None
    scrapeyard_name: Optional[str] = None
    gso_id: Optional[int] = None
    gso_name: Optional[str] = None
    security_id: Optional[int] = None
    security_name: Optional[str] = None
    admin_name: Optional[str] = None
    employees: List[EmployeeSummary] = []
