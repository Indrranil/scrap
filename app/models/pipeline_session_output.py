from sqlalchemy import Column, Integer, String, BigInteger
from database.connection import Base

class PipelineSessionOutput(Base):
    __tablename__ = "pipeline_session_output"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pipeline_session_id = Column(Integer, ForeignKey('pipeline_session.id'))
    name = Column(String(255))
    created_at = Column(BigInteger)
    ended_at = Column(BigInteger)
    is_usable = Column(Integer)
