from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.enums import AppRole, RejectionReasonType, TransferStatus


class LoginRequest(BaseModel):
    login_id: str
    password: str
    app_role: Optional[AppRole] = None


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
    admin_name: Optional[str] = None
    employees: List[EmployeeSummary] = []
