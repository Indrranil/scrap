from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class VendorItemAssignment(BaseModel):
    item_id: int
    rate_inr: Decimal = Field(..., ge=0)


class VendorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    vendor_code: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    contact_person: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    gst_number: Optional[str] = Field(None, max_length=50)
    items: List[VendorItemAssignment] = Field(default_factory=list)


class VendorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    vendor_code: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    contact_person: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    gst_number: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class VendorResponse(BaseModel):
    id: int
    name: str
    vendor_code: Optional[str] = None
    email: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    gst_number: Optional[str] = None
    is_active: bool
    created_at: int
    updated_at: Optional[int] = None

    class Config:
        from_attributes = True


class VendorSummaryResponse(BaseModel):
    """Minimal vendor info for Security dropdown."""

    id: int
    name: str
    vendor_code: Optional[str] = None

    class Config:
        from_attributes = True


class VendorListResponse(BaseModel):
    total: int
    items: List[VendorResponse]


class VendorSummaryListResponse(BaseModel):
    total: int
    items: List[VendorSummaryResponse]


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
