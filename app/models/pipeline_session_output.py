from sqlalchemy import Column, Integer, String, ForeignKey
from app.database.connection import Base


class PipelineSessionOutput(Base):
    __tablename__ = "pipeline_session_output"

    id = Column(Integer, primary_key=True, index=True)
    pipeline_session_id = Column(Integer, ForeignKey("pipeline_session.id"))
    name = Column(String(100))
    created_at = Column(Integer)
    ended_at = Column(Integer, nullable=True)
    is_usable = Column(Integer, default=1)
