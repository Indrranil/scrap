import enum

from sqlalchemy import BigInteger, Column, Enum, Integer, String

from app.database.connection import Base


class MachineType(str, enum.Enum):
    weight_machine = "weight machine"
    perforation = "perforation"
    rejector = "rejector"


class Machine(Base):
    __tablename__ = "machine"

    id = Column(Integer, primary_key=True, index=True)
    mid = Column(String(255))
    name = Column(String(255))
    machine_type = Column(String(255))
    created_at = Column(BigInteger)
    is_usable = Column(Integer)
