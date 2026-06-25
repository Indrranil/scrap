from typing import List

from pydantic import BaseModel

from app.schemas.auth import EmployeeSummary


class EmployeeListResponse(BaseModel):
    total: int
    items: List[EmployeeSummary]
