from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.auth import EmployeeSummary


class PlantCreate(BaseModel):
    code: Optional[str] = None
    name: str
    login_id: str
    password: str
    qr_location: int
    address: Optional[str] = None
    employee_names: List[str] = Field(default_factory=list)


class PlantUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    login_id: Optional[str] = None
    password: Optional[str] = None
    qr_location: Optional[int] = None
    address: Optional[str] = None
    employee_names: Optional[List[str]] = None


class PlantResponse(BaseModel):
    id: int
    code: Optional[str] = None
    name: str
    login_id: str
    qr_location: int
    address: Optional[str] = None
    is_active: bool
    employees: List[EmployeeSummary] = []

    class Config:
        from_attributes = True


class PlantListResponse(BaseModel):
    total: int
    items: List[PlantResponse]
