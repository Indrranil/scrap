rom sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, Enum, Text
from database.connection import Base

class OutputUnitStatus(enum.Enum):
    idle = "idle"
    ready = "ready"
    analysing = "analysing"
    success = "success"
    error = "error"

class PipelineSessionOutputUnit(Base):
    __tablename__ = "pipeline_session_output_unit"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pipeline_session_output_id = Column(Integer, ForeignKey('pipeline_session_output.id'))
    property_reference_id = Column(Integer, ForeignKey('general_property.id'))
    name = Column(String(255))
    output_key = Column(String(255))
    output_value = Column(String(255))
    status = Column(Enum(OutputUnitStatus))
    created_at = Column(BigInteger)
    is_usable = Column(Integer)