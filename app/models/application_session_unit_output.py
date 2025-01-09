from sqlalchemy import Column, Integer, String, BigInteger
from database.connection import Base

class ApplicationSessionUnitOutput(Base):
    __tablename__ = "application_session_unit_output"
    id = Column(Integer, primary_key=True, index=True)
    application_session_unit_id = Column(Integer)
    name = Column(String(255))
    output_key = Column(String(255))
    output_value = Column(String(255))
    created_at = Column(BigInteger)
    is_usable = Column(Integer)