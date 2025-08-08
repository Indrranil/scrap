from typing import Literal

from pydantic import BaseModel

StatusTypes = Literal[
    "start",
    "starting",
    "started",
    "idle",
    "running",
    "kill",
    "killing",
    "killed",
    "stop",
    "stopping",
    "stopped",
    "error",
]


class ApplicationStatusLogCreate(BaseModel):
    application_container_id: str
    value: StatusTypes


class ApplicationStatusLogResponse(ApplicationStatusLogCreate):
    id: int
    created_at: int

    class Config:
        from_attributes = True
