from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.application import Application as ApplicationModel
from app.schemas.application import Application, ApplicationCreate
from app.services.base import CRUDBase
from app.utils.application import check_duplicate_name


class ApplicationService(
    CRUDBase[ApplicationModel, ApplicationCreate, ApplicationCreate]
):
    """
    Application-specific CRUD service with custom business logic.
    """

    def __init__(self):
        super().__init__(ApplicationModel)

    def create(self, db: Session, *, obj_in: ApplicationCreate) -> ApplicationModel:
        """
        Create a new application with duplicate name checking.

        Args:
            db: Database session
            obj_in: Application creation data

        Returns:
            Created application instance

        Raises:
            HTTPException: If application name already exists
        """
        # Check for duplicate name
        if check_duplicate_name(db, obj_in.name):
            raise HTTPException(
                status_code=400, detail="Application with this name already exists"
            )

        # Use parent create method
        return super().create(db, obj_in=obj_in)


# Create a singleton instance
application_service = ApplicationService()
