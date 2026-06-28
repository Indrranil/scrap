from typing import Optional

from fastapi import APIRouter, Depends, Header, Query, Request
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_roles
from app.database.connection import get_db
from app.schemas.item import ShopfloorItemListResponse, ShopfloorItemResponse
from app.schemas.transfer import (
    DispatchRequest,
    ManualDispatchRequest,
    TransferListResponse,
    TransferResponse,
)
from app.services.item_master import item_master_service
from app.services.transfer import transfer_service

router = APIRouter(prefix="/v1/shopfloor", tags=["shopfloor"])


@router.get("/items", response_model=ShopfloorItemListResponse)
def list_manual_items(
    _: bool = Depends(require_roles(["shopfloor"])),
    db: Session = Depends(get_db),
):
    """List active EA items available for manual dispatch."""
    _, items = item_master_service.list_items(
        db, uom="EA", is_active=True, skip=0, limit=500
    )
    return ShopfloorItemListResponse(
        items=[
            ShopfloorItemResponse(
                id=i.id,
                plu_code=i.plu_code,
                item_code=i.item_code,
                name=i.name,
                uom=i.uom,
                is_shreddable=i.is_shreddable,
            )
            for i in items
        ]
    )


@router.post("/dispatch", response_model=TransferResponse)
def dispatch_material(
    body: DispatchRequest,
    request: Request,
    _: bool = Depends(require_roles(["shopfloor"])),
    db: Session = Depends(get_db),
):
    """Confirm QR dispatch. Logged-in plant must match QR location."""
    user = get_current_user(request)
    return transfer_service.dispatch(db, user["plant_id"], body)


@router.post("/dispatch/manual", response_model=TransferResponse)
def dispatch_material_manual(
    body: ManualDispatchRequest,
    request: Request,
    _: bool = Depends(require_roles(["shopfloor"])),
    db: Session = Depends(get_db),
):
    """Manual dispatch for EA items that cannot be weighed."""
    user = get_current_user(request)
    return transfer_service.dispatch_manual(db, user["plant_id"], body)


@router.get("/rejected", response_model=TransferListResponse)
def list_rejected(
    request: Request,
    item_code: Optional[str] = None,
    material_name: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _: bool = Depends(require_roles(["shopfloor"])),
    db: Session = Depends(get_db),
):
    """List rejected transfers awaiting acknowledgement."""
    user = get_current_user(request)
    total, items = transfer_service.list_transfers(
        db,
        shopfloor_plant_id=user["plant_id"],
        item_code=item_code,
        material_name=material_name,
        rejected_only=True,
        skip=(page - 1) * page_size,
        limit=page_size,
    )
    return TransferListResponse(total=total, items=items)


@router.post("/rejected/{transfer_id}/acknowledge", response_model=TransferResponse)
def acknowledge_rejection(
    transfer_id: int,
    request: Request,
    employee_id: int = Header(..., alias="X-Employee-Id"),
    _: bool = Depends(require_roles(["shopfloor"])),
    db: Session = Depends(get_db),
):
    """Acknowledge a rejected dispatch."""
    user = get_current_user(request)
    return transfer_service.acknowledge(
        db, user["plant_id"], transfer_id, employee_id
    )


@router.get("/gso-rejected", response_model=TransferListResponse)
def list_gso_rejected(
    request: Request,
    item_code: Optional[str] = None,
    material_name: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _: bool = Depends(require_roles(["shopfloor"])),
    db: Session = Depends(get_db),
):
    """List GSO-rejected transfers awaiting acknowledgement."""
    user = get_current_user(request)
    total, items = transfer_service.list_transfers(
        db,
        shopfloor_plant_id=user["plant_id"],
        item_code=item_code,
        material_name=material_name,
        gso_rejected_only=True,
        skip=(page - 1) * page_size,
        limit=page_size,
    )
    return TransferListResponse(total=total, items=items)


@router.post("/gso-rejected/{transfer_id}/acknowledge", response_model=TransferResponse)
def acknowledge_gso_rejection(
    transfer_id: int,
    request: Request,
    employee_id: int = Header(..., alias="X-Employee-Id"),
    _: bool = Depends(require_roles(["shopfloor"])),
    db: Session = Depends(get_db),
):
    """Acknowledge a GSO-rejected dispatch."""
    user = get_current_user(request)
    return transfer_service.acknowledge_gso_rejection(
        db, user["plant_id"], transfer_id, employee_id
    )
