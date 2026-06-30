from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.database.connection import get_db
from app.schemas.vendor import (
    VendorCreate,
    VendorItemCreate,
    VendorItemListResponse,
    VendorItemResponse,
    VendorItemUpdate,
    VendorListResponse,
    VendorResponse,
    VendorUpdate,
)
from app.services.vendor import vendor_service

router = APIRouter(prefix="/v1/vendors", tags=["vendors"])


@router.get("", response_model=VendorListResponse)
def list_vendors(
    search: Optional[str] = None,
    _: bool = Depends(require_roles(["admin", "security"])),
    db: Session = Depends(get_db),
):
    items = vendor_service.list_vendors(db, search=search)
    return VendorListResponse(total=len(items), items=items)


@router.post("", response_model=VendorResponse, status_code=201)
def create_vendor(
    body: VendorCreate,
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    return vendor_service.create_vendor(db, body)


@router.get("/{vendor_id}", response_model=VendorResponse)
def get_vendor(
    vendor_id: int,
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    return vendor_service.get_vendor(db, vendor_id)


@router.patch("/{vendor_id}", response_model=VendorResponse)
def update_vendor(
    vendor_id: int,
    body: VendorUpdate,
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    return vendor_service.update_vendor(db, vendor_id, body)


@router.delete("/{vendor_id}", response_model=VendorResponse)
def delete_vendor(
    vendor_id: int,
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    return vendor_service.delete_vendor(db, vendor_id)


@router.get("/{vendor_id}/items", response_model=VendorItemListResponse)
def list_vendor_items(
    vendor_id: int,
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    total, items = vendor_service.list_vendor_items(db, vendor_id)
    return VendorItemListResponse(total=total, items=items)


@router.post("/{vendor_id}/items", response_model=VendorItemResponse, status_code=201)
def add_vendor_item(
    vendor_id: int,
    body: VendorItemCreate,
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    return vendor_service.add_vendor_item(db, vendor_id, body)


@router.patch(
    "/{vendor_id}/items/{vendor_item_id}",
    response_model=VendorItemResponse,
)
def update_vendor_item(
    vendor_id: int,
    vendor_item_id: int,
    body: VendorItemUpdate,
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    return vendor_service.update_vendor_item(db, vendor_id, vendor_item_id, body)


@router.delete("/{vendor_id}/items/{vendor_item_id}", status_code=204)
def remove_vendor_item(
    vendor_id: int,
    vendor_item_id: int,
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    vendor_service.remove_vendor_item(db, vendor_id, vendor_item_id)
