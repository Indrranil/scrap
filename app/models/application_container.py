from sqlalchemy import Column, Integer, String, BigInteger
from database.connection import Base

class ApplicationContainer(Base):
    __tablename__ = "application_container"
    id = Column(String(255), primary_key=True, index=True)
    application_id = Column(Integer)
    created_at = Column(BigInteger)