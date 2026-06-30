from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_roles
from app.database.connection import get_db
from app.schemas.material_sale import (
    AvailableMaterialListResponse,
    MaterialSaleCreate,
    MaterialSaleListResponse,
    MaterialSaleResponse,
)
from app.services.inventory import inventory_service
from app.services.scrapeyard import scrapeyard_service
from app.services.shred import material_sale_service

router = APIRouter(prefix="/v1/security", tags=["security"])


def _parse_date(date_str: Optional[str]) -> Optional[int]:
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return int(dt.timestamp())
    except ValueError:
        return None


@router.get("/available-materials", response_model=AvailableMaterialListResponse)
def list_available_materials(
    item_code: Optional[str] = None,
    material_name: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _: bool = Depends(require_roles(["security"])),
    db: Session = Depends(get_db),
):
    """List materials available for sale."""
    scrapeyard = scrapeyard_service.get_active(db)
    total, items = inventory_service.get_available(
        db,
        scrapeyard.id,
        item_code=item_code,
        material_name=material_name,
        skip=(page - 1) * page_size,
        limit=page_size,
    )
    return AvailableMaterialListResponse(total=total, items=items)


@router.post("/sales", response_model=MaterialSaleResponse, status_code=201)
def create_sale(
    body: MaterialSaleCreate,
    request: Request,
    _: bool = Depends(require_roles(["security"])),
    db: Session = Depends(get_db),
):
    """Record a material sale (pending admin approval)."""
    user = get_current_user(request)
    return material_sale_service.create_sale(db, user["security_id"], body)


@router.get("/sales/history", response_model=MaterialSaleListResponse)
def list_sale_history(
    item_code: Optional[str] = None,
    material_name: Optional[str] = None,
    vendor_id: Optional[int] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _: bool = Depends(require_roles(["security"])),
    db: Session = Depends(get_db),
):
    """List material sale history."""
    scrapeyard = scrapeyard_service.get_active(db)
    date_to_ts = _parse_date(date_to)
    if date_to_ts:
        date_to_ts += 86399
    total, items = material_sale_service.list_sales(
        db,
        scrapeyard.id,
        item_code=item_code,
        material_name=material_name,
        vendor_id=vendor_id,
        status=status,
        date_from=_parse_date(date_from),
        date_to=date_to_ts,
        skip=(page - 1) * page_size,
        limit=page_size,
    )
    return MaterialSaleListResponse(total=total, items=items)


@router.get("/sales/{sale_id}", response_model=MaterialSaleResponse)
def get_sale(
    sale_id: int,
    _: bool = Depends(require_roles(["security"])),
    db: Session = Depends(get_db),
):
    """Get material sale detail with timeline."""
    return material_sale_service.get_sale(db, sale_id)
