from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_roles
from app.database.connection import get_db
from app.schemas.material_sale import (
    MaterialSaleListResponse,
    MaterialSaleReject,
    MaterialSaleResponse,
)
from app.services.scrapeyard import scrapeyard_service
from app.services.shred import material_sale_service

router = APIRouter(prefix="/v1/material-sales", tags=["material-sales-admin"])


def _parse_date(date_str: Optional[str]) -> Optional[int]:
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return int(dt.timestamp())
    except ValueError:
        return None


def _parse_admin_id(user: dict) -> int:
    sub = user.get("id", "")
    if not sub.startswith("admin:"):
        raise ValueError("Not an admin user")
    return int(sub.split(":", 1)[1])


@router.get("", response_model=MaterialSaleListResponse)
def list_material_sales(
    item_code: Optional[str] = None,
    material_name: Optional[str] = None,
    vendor_id: Optional[int] = None,
    status: Optional[str] = Query("pending"),
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    """List material sales for admin approval."""
    scrapeyard = scrapeyard_service.get_active(db)
    total, items = material_sale_service.list_sales(
        db,
        scrapeyard.id,
        item_code=item_code,
        material_name=material_name,
        vendor_id=vendor_id,
        status=status,
        date_from=_parse_date(date_from),
        date_to=_parse_date(date_to),
        skip=(page - 1) * page_size,
        limit=page_size,
    )
    return MaterialSaleListResponse(total=total, items=items)


@router.get("/{sale_id}", response_model=MaterialSaleResponse)
def get_material_sale(
    sale_id: int,
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    """Get material sale detail for approval."""
    return material_sale_service.get_sale(db, sale_id)


@router.post("/{sale_id}/approve", response_model=MaterialSaleResponse)
def approve_material_sale(
    sale_id: int,
    request: Request,
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    """Approve a pending material sale."""
    user = get_current_user(request)
    admin_id = _parse_admin_id(user)
    return material_sale_service.approve_sale(db, sale_id, admin_id)


@router.post("/{sale_id}/reject", response_model=MaterialSaleResponse)
def reject_material_sale(
    sale_id: int,
    body: MaterialSaleReject,
    request: Request,
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    """Reject a pending material sale and restore inventory."""
    user = get_current_user(request)
    admin_id = _parse_admin_id(user)
    return material_sale_service.reject_sale(db, sale_id, admin_id, body.reason)
