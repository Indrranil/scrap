from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.auth import EmployeeSummary


class ScrapeyardUpdate(BaseModel):
    name: Optional[str] = None
    login_id: Optional[str] = None
    password: Optional[str] = None
    employee_names: Optional[List[str]] = None


class ScrapeyardResponse(BaseModel):
    id: int
    name: str
    login_id: str
    is_active: bool
    employees: List[EmployeeSummary] = []

    class Config:
        from_attributes = True
