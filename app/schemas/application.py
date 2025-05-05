from pydantic import BaseModel, field_validator


class ApplicationBase(BaseModel):
    name: str
    is_usable: int = 1

    @field_validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Value error, Name cannot be empty")
        if len(v) > 255:
            raise ValueError("Value error, Name cannot exceed 255 characters")
        return v.strip()


class ApplicationCreate(ApplicationBase):
    pass


class Application(ApplicationBase):
    id: int
    created_at: int

    class Config:
        from_attributes = True
