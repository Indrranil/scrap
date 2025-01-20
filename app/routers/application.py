from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List
import time

from database.connection import get_db
from schemas.application import ApplicationCreate, Application
from models.application import Application as ApplicationModel

router = APIRouter(prefix="/v1/application", tags=["application"])

@router.post("/new", response_model=Application, status_code=201)
async def create_application(
    application: ApplicationCreate,
    db: Session = Depends(get_db)
):
    try:
        db.begin()
        
        timestamp = int(time.time())
        new_application = ApplicationModel(
            name=application.name,
            created_at=timestamp,
            is_usable=1
        )
        
        db.add(new_application)
        db.commit()
        db.refresh(new_application)
        
        return new_application
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating application: {str(e)}"
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

@router.get("/", response_model=List[Application])
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

@router.patch("/{application_id}", response_model=Application)
async def update_application(
    application_id: int,
    application: ApplicationCreate,
    db: Session = Depends(get_db)
):
    try:
        db.begin()
        
        existing_application = db.query(ApplicationModel).filter(
            ApplicationModel.id == application_id,
            ApplicationModel.is_usable == 1
        ).first()
        
        if not existing_application:
            raise HTTPException(
                status_code=404,
                detail=f"Application with ID {application_id} not found"
            )
            
        # Update fields
        existing_application.name = application.name
        
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