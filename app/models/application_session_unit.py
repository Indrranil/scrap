from sqlalchemy import Column, Integer, String, BigInteger
from database.connection import Base

class ApplicationSessionUnit(Base):
    __tablename__ = "application_session_unit"
    id = Column(Integer, primary_key=True, index=True)
    application_session_id = Column(Integer)
    name = Column(String(255))
    created_at = Column(BigInteger)
    ended_at = Column(BigInteger)
    is_usable = Column(Integer)