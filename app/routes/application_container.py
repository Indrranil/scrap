from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import time
from database.connection import get_db
from models.application_container import ApplicationContainer
from schemas.application_container import ApplicationContainerCreate, ApplicationContainerResponse

router = APIRouter(prefix="/application-containers", tags=["application_containers"])

@router.post("/", response_model=ApplicationContainerResponse)
def create_container(container: ApplicationContainerCreate, db: Session = Depends(get_db)):
    db_container = ApplicationContainer(**container.dict(), created_at=int(time.time()))
    db.add(db_container)
    db.commit()
    db.refresh(db_container)
    return db_container

@router.get("/{container_id}", response_model=ApplicationContainerResponse)
def get_container(container_id: str, db: Session = Depends(get_db)):
    container = db.query(ApplicationContainer).filter(ApplicationContainer.id == container_id).first()
    if not container:
        raise HTTPException(status_code=404, detail="Container not found")
    return container

@router.get("/", response_model=List[ApplicationContainerResponse])
def list_containers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    containers = db.query(ApplicationContainer).offset(skip).limit(limit).all()
    return containers
