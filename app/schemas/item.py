from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.enums import MaterialState


class ItemMasterCreate(BaseModel):
    plu_code: str = Field(..., min_length=1, max_length=20)
    item_code: Optional[str] = Field(None, max_length=20)
    name: str = Field(..., min_length=1, max_length=500)
    uom: str = Field(..., min_length=1, max_length=10)
    is_shreddable: bool = False


class ItemMasterUpdate(BaseModel):
    plu_code: Optional[str] = Field(None, min_length=1, max_length=20)
    item_code: Optional[str] = Field(None, max_length=20)
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    uom: Optional[str] = Field(None, min_length=1, max_length=10)
    is_shreddable: Optional[bool] = None
    is_active: Optional[bool] = None


class ItemMasterResponse(BaseModel):
    id: int
    plu_code: str
    item_code: Optional[str] = None
    name: str
    uom: str
    is_shreddable: bool
    is_active: bool
    created_at: int
    updated_at: int

    class Config:
        from_attributes = True


class ItemMasterListResponse(BaseModel):
    total: int
    items: List[ItemMasterResponse]


class ShopfloorItemResponse(BaseModel):
    id: int
    plu_code: str
    item_code: Optional[str] = None
    name: str
    uom: str
    is_shreddable: bool

    class Config:
        from_attributes = True


class ShopfloorItemListResponse(BaseModel):
    items: List[ShopfloorItemResponse]
