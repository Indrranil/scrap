from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class ShredSaveRequest(BaseModel):
    transfer_id: int
    quantity_pre_shred: Decimal = Field(..., gt=0)
    quantity_post_shred: Decimal = Field(..., gt=0)
    employee_id: int


class ShredLogResponse(BaseModel):
    id: int
    transfer_id: int
    scrapeyard_id: int
    input_plu_code: str
    input_name: str
    output_item_code: str
    output_name: str
    quantity_pre_shred: Decimal
    quantity_post_shred: Decimal
    process_loss: Decimal
    shredded_at: int

    class Config:
        from_attributes = True


class ShredLogListResponse(BaseModel):
    total: int
    items: List[ShredLogResponse]


class ShredQueueItem(BaseModel):
    transfer_id: int
    item_code: str
    item_name: str
    uom: str
    available_qty: Decimal


class ShredQueueListResponse(BaseModel):
    total: int
    items: List[ShredQueueItem]


class ReadyForSaleItem(BaseModel):
    item_code: str
    material_name: str
    available_qty: Decimal
    uom: str


class ReadyForSaleListResponse(BaseModel):
    total: int
    items: List[ReadyForSaleItem]
