import logging
from typing import List

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.application import ApplicationCreate, Application
from app.services.application import application_service

router = APIRouter(prefix="/v1/application", tags=["application"])

logger = logging.getLogger(__name__)


@router.post("/new", response_model=Application, status_code=201)
async def create_application(
        application: ApplicationCreate,
        db: Session = Depends(get_db)
):
    """Create a new application."""
    return application_service.create(db, obj_in=application)


@router.get("/all", response_model=List[Application])
async def get_all_applications(
        db: Session = Depends(get_db)
):
    """Get all active applications."""
    return application_service.get_all(db)


@router.get("/{application_id}", response_model=Application)
async def get_application(
        application_id: int,
        db: Session = Depends(get_db)
):
    """Get a specific application by ID."""
    return application_service.get_or_404(db, application_id)


@router.patch("/{application_id}", response_model=Application)
async def update_application(
        application_id: int,
        application: ApplicationCreate,
        db: Session = Depends(get_db)
):
    """Update an existing application."""
    db_obj = application_service.get_or_404(db, application_id)
    return application_service.update(db, db_obj=db_obj, obj_in=application)


@router.delete("/{application_id}", response_model=Application)
async def delete_application(
        application_id: int,
        db: Session = Depends(get_db)
):
    """Soft delete an application."""
    return application_service.remove(db, id=application_id)
