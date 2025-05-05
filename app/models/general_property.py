from sqlalchemy import Column, Integer, String, BigInteger, Enum
from app.database.connection import Base
import enum


class PropertyType(enum.Enum):
    machine = "machine"
    pipeline = "pipeline"
    application = "application"
    pipeline_input = "pipeline_input"


class GeneralProperty(Base):
    __tablename__ = "general_property"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    referrer_id = Column(Integer)
    property_type = Column(Enum(PropertyType))
    property_label = Column(String(255))
    property_key = Column(String(255))
    property_value = Column(String(255))
    tags = Column(String(255))
    created_at = Column(BigInteger)
    is_usable = Column(Integer)
