# models/pipeline_session.py
from sqlalchemy import Column, Integer, String, ForeignKey
from database.connection import Base

class PipelineSession(Base):
    __tablename__ = "pipeline_session"

    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(Integer, ForeignKey("application.id"))  # Changed from application_id
    pipeline_input_id = Column(Integer)
    name = Column(String)
    created_by = Column(Integer)
    created_at = Column(Integer)
    ended_at = Column(Integer, nullable=True)
    is_usable = Column(Integer, default=1)