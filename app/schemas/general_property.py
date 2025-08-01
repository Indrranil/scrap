from typing import Literal, Optional

from pydantic import BaseModel


class GeneralPropertyBase(BaseModel):
    referrer_id: int
    property_type: Literal["machine", "pipeline", "application", "pipeline_input"]
    property_label: str
    property_key: str
    property_value: str
    tags: Optional[str] = ""
    is_usable: int = 1


class GeneralPropertyUpdate(BaseModel):
    referrer_id: Optional[int] = None
    property_type: Optional[
        Literal["machine", "pipeline", "application", "pipeline_input"]
    ] = None
    property_label: Optional[str] = None
    property_key: Optional[str] = None
    property_value: Optional[str] = None
    tags: Optional[str] = None
    is_usable: Optional[int] = None


class GeneralPropertyResponse(GeneralPropertyBase):
    id: int
    created_at: int

    class Config:
        from_attributes = True
