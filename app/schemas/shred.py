from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class ShredSaveRequest(BaseModel):
    transfer_id: int
    quantity_kg: Decimal = Field(..., gt=0)
    employee_id: int


class ShredLogResponse(BaseModel):
    id: int
    transfer_id: int
    scrapeyard_id: int
    input_plu_code: str
    input_name: str
    output_item_code: str
    output_name: str
    quantity_kg: Decimal
    shredded_at: int

    class Config:
        from_attributes = True


class ShredLogListResponse(BaseModel):
    total: int
    items: List[ShredLogResponse]
