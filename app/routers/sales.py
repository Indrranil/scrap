from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.database.connection import get_db
from app.schemas.sale import SaleCreate, SaleListResponse, SaleResponse
from app.services.reporting import sale_service

router = APIRouter(prefix="/v1/sales", tags=["sales"])


@router.post("", response_model=SaleResponse, status_code=201)
def create_sale(
    body: SaleCreate,
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    """Record a post-shredding scrap sale."""
    return sale_service.create_sale(db, body)


@router.get("", response_model=SaleListResponse)
def list_sales(
    plant_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    """List scrap sales."""
    total, items = sale_service.list_sales(
        db, plant_id=plant_id, skip=(page - 1) * page_size, limit=page_size
    )
    return SaleListResponse(total=total, items=items)
