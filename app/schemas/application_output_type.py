from pydantic import BaseModel

class ApplicationOutputTypeCreate(BaseModel):
    application_id: int
    key_name: str
    is_usable: int = 1

class ApplicationOutputTypeResponse(ApplicationOutputTypeCreate):
    id: int
    created_at: int

    class Config:
        from_attributes = True