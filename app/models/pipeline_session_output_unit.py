# models/pipeline_session_output_unit.py
from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from app.database.connection import Base
import enum


class UnitStatus(str, enum.Enum):
    idle = 'idle'
    ready = 'ready'
    analysing = 'analysing'
    success = 'success'
    error = 'error'


class PipelineSessionOutputUnit(Base):
    __tablename__ = "pipeline_session_output_unit"

    id = Column(Integer, primary_key=True, index=True)
    pipeline_session_output_id = Column(Integer, ForeignKey("pipeline_session_output.id"))
    property_reference_id = Column(Integer, ForeignKey("general_property.id"))
    name = Column(String(100))
    output_key = Column(String(100))
    output_value = Column(String(100))
    status = Column(Enum(UnitStatus), default=UnitStatus.success)
    created_at = Column(Integer)
    is_usable = Column(Integer, default=1)
