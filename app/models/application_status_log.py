import enum

from sqlalchemy import BigInteger, Column, Enum, ForeignKey, Integer, String

from app.database.connection import Base


class ApplicationStatus(enum.Enum):
    start = "start"
    starting = "starting"
    started = "started"
    idle = "idle"
    running = "running"
    kill = "kill"
    killing = "killing"
    killed = "killed"
    stop = "stop"
    stopping = "stopping"
    stopped = "stopped"
    error = "error"


class ApplicationStatusLog(Base):
    __tablename__ = "application_status_log"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    application_container_id = Column(
        String(255), ForeignKey("application_container.id")
    )
    value = Column(Enum(ApplicationStatus))  # type: ignore
    created_at = Column(BigInteger)
