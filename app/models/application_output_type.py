from sqlalchemy import Column, Integer, String, BigInteger
from database.connection import Base

class ApplicationOutputType(Base):
    __tablename__ = "application_output_type"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer)
    key_name = Column(String(255))
    is_usable = Column(Integer)
    created_at = Column(BigInteger)
