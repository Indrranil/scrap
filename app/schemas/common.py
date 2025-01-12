# schemas/common.py
from pydantic import BaseModel
from typing import List

class PropertyItem(BaseModel):
    id: int
    property_label: str
    property_key: str
    property_value: str
    created_at: int

class GenericItemResponse(BaseModel):
    id: int
    name: str
    created_at: int
    properties: List[PropertyItem]

class GenericListResponse(BaseModel):
    total: int
    items: List[GenericItemResponse]