from pydantic import BaseModel
from typing import Optional, Literal

PropertyType = Literal['machine', 'pipeline', 'application', 'pipeline_input']

class PropertyDescriptionBase(BaseModel):
    property_type: PropertyType
    description: str
    property_key: str
    property_value_type: str
    property_label: str
    is_usable: int

class PropertyDescriptionCreate(PropertyDescriptionBase):
    pass

class PropertyDescription(PropertyDescriptionBase):
    id: int
    created_at: int
    class Config:
        from_attributes = True