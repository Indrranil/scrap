import logging
import time
from typing import List

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.application import Application as ApplicationModel
from app.schemas.application import ApplicationCreate, Application
from app.utils.application import check_duplicate_name

router = APIRouter(prefix="/v1/application", tags=["application"])

logger = logging.getLogger(__name__)


@router.post("/new", response_model=Application, status_code=201)
async def create_application(
        application: ApplicationCreate,
        db: Session = Depends(get_db)
):
    try:
        logger.debug(f"Creating application with data: {application.dict()}")

        # Check for duplicate name
        if check_duplicate_name(db, application.name):
            logger.debug("Duplicate name found")
            raise HTTPException(
                status_code=400,
                detail="Application with this name already exists"
            )

        # Create new application
        new_application = ApplicationModel(
            name=application.name,
            created_at=int(time.time()),
            is_usable=application.is_usable
        )
        logger.debug(f"Created model instance: {vars(new_application)}")

        db.add(new_application)
        db.commit()
        logger.debug("Database commit successful")
        db.refresh(new_application)
        logger.debug(f"Refreshed model instance: {vars(new_application)}")

        return new_application

    except HTTPException as he:
        # Handle HTTP exceptions separately
        db.rollback()
        raise he
    except Exception as e:
        logger.error(f"Error in create_application: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating application: {str(e)}"
        )


@router.get("/all", response_model=List[Application])
async def get_all_applications(db: Session = Depends(get_db)):
    try:
        applications = db.query(ApplicationModel).filter(
            ApplicationModel.is_usable == 1
        ).all()

        return applications

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching applications: {str(e)}"
        )


@router.get("/{application_id}", response_model=Application)
async def get_application(
        application_id: int,
        db: Session = Depends(get_db)
):
    try:
        application = db.query(ApplicationModel).filter(
            ApplicationModel.id == application_id,
            ApplicationModel.is_usable == 1
        ).first()

        if not application:
            raise HTTPException(
                status_code=404,
                detail=f"Application with ID {application_id} not found"
            )

        return application

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching application: {str(e)}"
        )


@router.patch("/{application_id}", response_model=Application)
async def update_application(
        application_id: int,
        application: ApplicationCreate,
        db: Session = Depends(get_db)
):
    try:
        existing_application = db.query(ApplicationModel).filter(
            ApplicationModel.id == application_id,
            ApplicationModel.is_usable == 1
        ).first()

        if not existing_application:
            raise HTTPException(
                status_code=404,
                detail=f"Application with ID {application_id} not found"
            )

        # Check for duplicate name
        if check_duplicate_name(db, application.name, exclude_id=application_id):
            raise HTTPException(
                status_code=400,
                detail="Application with this name already exists"
            )

        # Update fields using setattr
        setattr(existing_application, 'name', application.name)
        setattr(existing_application, 'is_usable', application.is_usable)

        db.commit()
        db.refresh(existing_application)

        return existing_application

    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error updating application: {str(e)}"
        )


@router.delete("/{application_id}")
async def delete_application(
        application_id: int,
        db: Session = Depends(get_db)
):
    try:
        db.begin()

        application = db.query(ApplicationModel).filter(
            ApplicationModel.id == application_id,
            ApplicationModel.is_usable == 1
        ).first()

        if not application:
            raise HTTPException(
                status_code=404,
                detail=f"Application with ID {application_id} not found"
            )

        # Soft delete
        application.is_usable = 0

        db.commit()

        return {
            "message": f"Application with ID {application_id} successfully deleted"
        }

    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting application: {str(e)}"
        )
