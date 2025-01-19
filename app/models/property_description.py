from sqlalchemy import Column, Integer, String, BigInteger, Enum
from database.connection import Base

class PropertyType(enum.Enum):
    machine = "machine"
    pipeline = "pipeline"
    application = "application"
    pipeline_input = "pipeline_input"

class PropertyDescription(Base):
    __tablename__ = "property_description"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    property_type = Column(Enum(PropertyType))
    description = Column(String(255))
    property_key = Column(String(255))
    property_value_type = Column(String(255))
    property_label = Column(String(255))
    created_at = Column(BigInteger)
    is_usable = Column(Integer)