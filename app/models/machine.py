from sqlalchemy import Column, Integer, String, Enum, BigInteger
from app.database.connection import Base
import enum


class MachineType(str, enum.Enum):
    weight_machine = "weight machine"
    perforation = "perforation"
    rejector = "rejector"


class Machine(Base):
    __tablename__ = "machine"

    id = Column(Integer, primary_key=True, index=True)
    mid = Column(String(255))
    name = Column(String(255))
    machine_type = Column(Enum(MachineType))
    created_at = Column(BigInteger)
    is_usable = Column(Integer)
