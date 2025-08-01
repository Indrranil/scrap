from pydantic import BaseModel


class ApplicationContainerCreate(BaseModel):
    id: str
    application_id: int


class ApplicationContainerResponse(ApplicationContainerCreate):
    created_at: int

    class Config:
        from_attributes = True
