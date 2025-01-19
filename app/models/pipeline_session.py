from sqlalchemy import Column, Integer, String, BigInteger
from database.connection import Base

class PipelineSession(Base):
    __tablename__ = "pipeline_session"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pipeline_id = Column(Integer, ForeignKey('pipeline.id'))
    pipeline_input_id = Column(Integer, ForeignKey('pipeline_input.id'))
    name = Column(String(255))
    created_by = Column(Integer)
    created_at = Column(BigInteger)
    ended_at = Column(BigInteger)
    is_usable = Column(Integer)