from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.auth import EmployeeSummary


class GsoUpdate(BaseModel):
    name: Optional[str] = None
    login_id: Optional[str] = None
    password: Optional[str] = None
    employee_names: Optional[List[str]] = None


class GsoResponse(BaseModel):
    id: int
    plant_id: int
    name: str
    login_id: str
    is_active: bool
    employees: List[EmployeeSummary] = []
    generated_password: Optional[str] = None

    class Config:
        from_attributes = True
