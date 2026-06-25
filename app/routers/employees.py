from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_roles
from app.database.connection import get_db
from app.models.employee_profile import EmployeeProfile
from app.schemas.auth import EmployeeSummary
from app.schemas.employee import EmployeeListResponse

router = APIRouter(prefix="/v1/employees", tags=["employees"])


@router.get("", response_model=EmployeeListResponse)
def list_employees(
    request: Request,
    db: Session = Depends(get_db),
    _: bool = Depends(require_roles(["shopfloor", "scrapeyard"])),
):
    """List active employee profiles for the logged-in plant."""
    user = get_current_user(request)
    plant_id = user.get("plant_id")
    employees = (
        db.query(EmployeeProfile)
        .filter(
            EmployeeProfile.plant_id == plant_id,
            EmployeeProfile.is_active.is_(True),
        )
        .all()
    )
    items = [EmployeeSummary(id=e.id, name=e.name) for e in employees]
    return EmployeeListResponse(total=len(items), items=items)
