from pydantic import BaseModel

class ApplicationSessionUnitOutputCreate(BaseModel):
    application_session_unit_id: int
    name: str
    output_key: str
    output_value: str
    is_usable: int = 1

class ApplicationSessionUnitOutputResponse(ApplicationSessionUnitOutputCreate):
    id: int
    created_at: int

    class Config:
        from_attributes = True