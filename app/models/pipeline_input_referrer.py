from sqlalchemy import Column, Integer, String, BigInteger
from database.connection import Base

class PipelineInputReferrer(Base):
    __tablename__ = "pipeline_input_referrer"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255))
    value = Column(String(255))
    pipeline_input_id = Column(Integer)
    created_at = Column(BigInteger)
    is_usable = Column(Integer)
