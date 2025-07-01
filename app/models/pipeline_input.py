from sqlalchemy import Column, Integer, String, BigInteger
from app.database.connection import Base


class PipelineInput(Base):
    __tablename__ = "pipeline_input"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    created_at = Column(BigInteger)
    is_usable = Column(Integer)
