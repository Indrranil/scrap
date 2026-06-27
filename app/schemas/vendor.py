from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class VendorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class VendorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None


class VendorResponse(BaseModel):
    id: int
    name: str
    is_active: bool
    created_at: int

    class Config:
        from_attributes = True


class VendorListResponse(BaseModel):
    total: int
    items: List[VendorResponse]


class VendorItemCreate(BaseModel):
    item_id: int
    rate_inr: Decimal = Field(..., ge=0)


class VendorItemUpdate(BaseModel):
    rate_inr: Decimal = Field(..., ge=0)


class VendorItemResponse(BaseModel):
    id: int
    vendor_id: int
    item_id: int
    plu_code: str
    item_code: Optional[str] = None
    item_name: str
    uom: str
    rate_inr: Decimal

    class Config:
        from_attributes = True


class VendorItemListResponse(BaseModel):
    total: int
    items: List[VendorItemResponse]
