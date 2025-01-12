from sqlalchemy import Column, Integer, String, BigInteger, Enum
from database.connection import Base

class GeneralProperty(Base):
    __tablename__ = "general_property"
    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer)
    property_type = Column(Enum('machine', 'pipeline', 'application', 'pipeline_input'))
    property_label = Column(String(255))
    property_key = Column(String(255))
    property_value = Column(String(255))
    created_at = Column(BigInteger)
    is_usable = Column(Integer)