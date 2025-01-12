from pydantic import BaseModel
from typing import Literal

class GeneralPropertyBase(BaseModel):
    referrer_id: int
    property_type: Literal['machine', 'pipeline', 'application', 'pipeline_input']
    property_label: str
    property_key: str
    property_value: str
    is_usable: int = 1

class GeneralPropertyResponse(GeneralPropertyBase):
    id: int
    created_at: int
    
    class Config:
        from_attributes = True