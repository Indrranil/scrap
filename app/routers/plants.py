from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.database.connection import get_db
from app.schemas.plant import PlantCreate, PlantListResponse, PlantResponse, PlantUpdate
from app.services.plant import plant_service

router = APIRouter(prefix="/v1/plants", tags=["plants"])


@router.get("", response_model=PlantListResponse)
def list_plants(
    search: Optional[str] = None,
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    """List all plants with optional search."""
    items = plant_service.list_plants(db, search=search)
    return PlantListResponse(total=len(items), items=items)


@router.post("", response_model=PlantResponse, status_code=201)
def create_plant(
    body: PlantCreate,
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    """Create a new plant with employee profiles."""
    return plant_service.create_plant(db, body)


@router.get("/{plant_id}", response_model=PlantResponse)
def get_plant(
    plant_id: int,
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    """Get plant detail."""
    return plant_service.get_plant(db, plant_id)


@router.patch("/{plant_id}", response_model=PlantResponse)
def update_plant(
    plant_id: int,
    body: PlantUpdate,
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    """Update plant and employee profiles."""
    return plant_service.update_plant(db, plant_id, body)


@router.delete("/{plant_id}", response_model=PlantResponse)
def delete_plant(
    plant_id: int,
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    """Soft-deactivate a plant."""
    return plant_service.delete_plant(db, plant_id)


@router.post("/{plant_id}/copy", response_model=PlantResponse, status_code=201)
def copy_plant(
    plant_id: int,
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    """Duplicate a plant configuration."""
    return plant_service.copy_plant(db, plant_id)
