from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class SaleCreate(BaseModel):
    transfer_id: int
    plant_id: int
    quantity_kg: Optional[Decimal] = None
    quantity_ea: Optional[Decimal] = None
    amount_inr: Decimal
    notes: Optional[str] = None


class SaleResponse(BaseModel):
    id: int
    transfer_id: int
    plant_id: int
    quantity_kg: Optional[Decimal] = None
    quantity_ea: Optional[Decimal] = None
    amount_inr: Decimal
    sold_at: int
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class SaleListResponse(BaseModel):
    total: int
    items: List[SaleResponse]
