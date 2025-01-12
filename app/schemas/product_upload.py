from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class ProductUploadCreate(BaseModel):
    variant_name: str = Field(..., alias="Variant Name")
    cld_barcode: str = Field(..., alias="CLD Barcode")
    form_factor: Optional[str] = Field(None, alias="Form Factor")
    product_name: Optional[str] = Field(None, alias="Product Name")
    variant_barcode: Optional[str] = Field(None, alias="Variant Barcode")
    material_code_front: Optional[str] = Field(None, alias="Material Code-Front")
    material_code_back: Optional[str] = Field(None, alias="Material Code-Back")
    price: Optional[str] = Field(None, alias="Price")
    usp: Optional[str] = Field(None, alias="USP")
    manufacturing_date: Optional[str] = Field(None, alias="Manufacturing Date")
    expiry_date: Optional[str] = Field(None, alias="Expiry Date")
    factory_code: Optional[str] = Field(None, alias="Factory Code")
    target_weight: Optional[float] = Field(None, alias="Target Weight (g)")
    tare_weight: Optional[float] = Field(None, alias="Tare Weight (g)")
    front_face : Optional[str] = Field(None, alias="Front Face")
    back_face : Optional[str] = Field(None, alias="Back Face")
    left_face : Optional[str] = Field(None, alias="Left Face")
    right_face : Optional[str] = Field(None, alias="Right Face")
    top_face : Optional[str] = Field(None, alias="Top Face")
    bottom_face : Optional[str] = Field(None, alias="Bottom Face")
    damage: Optional[str] = Field(None, alias="Damage")
    flap_open: Optional[str] = Field(None, alias="Flap Open")
    grease_dirt: Optional[str] = Field(None, alias="Grease Dirt")
    color_mismatch: Optional[str] = Field(None, alias="Color Mismatch")

    class Config:
        populate_by_name = True