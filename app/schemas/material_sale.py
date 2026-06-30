from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class AvailableMaterialItem(BaseModel):
    item_code: str
    material_name: str
    available_qty: Decimal
    uom: str


class AvailableMaterialListResponse(BaseModel):
    total: int
    items: List[AvailableMaterialItem]


class MaterialSaleCreate(BaseModel):
    item_code: str = Field(..., min_length=1)
    vendor_id: int
    vehicle_number: str = Field(..., min_length=1, max_length=50)
    quantity_sold: Decimal = Field(..., gt=0)
    total_weight_kg: Optional[Decimal] = Field(None, gt=0)
    employee_id: int


class MaterialSaleEventResponse(BaseModel):
    event_type: str
    actor_role: str
    employee_name: str
    quantity: Optional[Decimal] = None
    comment: Optional[str] = None
    created_at: int


class MaterialSaleResponse(BaseModel):
    id: int
    item_code: str
    item_name: str
    uom: str
    available_qty_at_sale: Optional[Decimal] = None
    quantity_sold: Decimal
    total_weight_kg: Optional[Decimal] = None
    vendor_id: int
    vendor_name: str
    vehicle_number: str
    amount_inr: Optional[Decimal] = None
    status: str
    display_status: str
    recorded_at: int
    events: List[MaterialSaleEventResponse] = []

    class Config:
        from_attributes = True


class MaterialSaleListItem(BaseModel):
    id: int
    item_code: str
    item_name: str
    uom: str
    quantity_sold: Decimal
    vendor_name: str
    status: str
    display_status: str
    recorded_at: int


class MaterialSaleListResponse(BaseModel):
    total: int
    items: List[MaterialSaleListItem]


class MaterialSaleReject(BaseModel):
    reason: str = Field(..., min_length=1)
