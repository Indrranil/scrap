from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.database.connection import get_db
from app.schemas.item import (
    ItemMasterCreate,
    ItemMasterCreateWithVendors,
    ItemMasterListResponse,
    ItemMasterResponse,
    ItemMasterUpdate,
    ItemMasterWithVendorsResponse,
    PostShredOptionListResponse,
)
from app.services.item_master import item_master_service

router = APIRouter(prefix="/v1/items", tags=["items"])


@router.get("", response_model=ItemMasterListResponse)
def list_items(
    search: Optional[str] = None,
    uom: Optional[str] = None,
    is_shreddable: Optional[bool] = None,
    is_p_item: Optional[bool] = None,
    is_active: Optional[bool] = True,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    total, items = item_master_service.list_items(
        db,
        search=search,
        uom=uom,
        is_shreddable=is_shreddable,
        is_p_item=is_p_item,
        is_active=is_active,
        skip=(page - 1) * page_size,
        limit=page_size,
    )
    return ItemMasterListResponse(total=total, items=items)


@router.get("/post-shred-options", response_model=PostShredOptionListResponse)
def list_post_shred_options(
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    """List ready-for-sale items for P-item post-shredding linkage."""
    total, items = item_master_service.list_post_shred_options(
        db,
        search=search,
        skip=(page - 1) * page_size,
        limit=page_size,
    )
    return PostShredOptionListResponse(total=total, items=items)


@router.post("/with-vendors", response_model=ItemMasterWithVendorsResponse, status_code=201)
def create_item_with_vendors(
    body: ItemMasterCreateWithVendors,
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    """Create an item and assign vendor rates in one transaction."""
    return item_master_service.create_item_with_vendors(db, body)


@router.post("", response_model=ItemMasterResponse, status_code=201)
def create_item(
    body: ItemMasterCreate,
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    return item_master_service.create_item(db, body)


@router.get("/{item_id}", response_model=ItemMasterResponse)
def get_item(
    item_id: int,
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    item = item_master_service.get_by_id(db, item_id)
    return ItemMasterResponse.model_validate(item)


@router.patch("/{item_id}", response_model=ItemMasterResponse)
def update_item(
    item_id: int,
    body: ItemMasterUpdate,
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    return item_master_service.update_item(db, item_id, body)


@router.delete("/{item_id}", response_model=ItemMasterResponse)
def delete_item(
    item_id: int,
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    return item_master_service.delete_item(db, item_id)
