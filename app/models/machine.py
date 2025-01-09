from sqlalchemy import Column, Integer, String, Enum, BigInteger
from database.connection import Base
import enum

class MachineType(str, enum.Enum):
    camera = "camera"
    server = "server"
    rejector = "rejector"

class Machine(Base):
    __tablename__ = "machine"

    id = Column(Integer, primary_key=True, index=True)
    mid = Column(String(255))
    factory_id = Column(String(255))
    plant_id = Column(String(255))
    location = Column(String(255))
    machine_type = Column(Enum(MachineType))
    created_at = Column(BigInteger)
    is_usable = Column(Integer)