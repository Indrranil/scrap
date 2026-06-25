from sqlalchemy import BigInteger, Column, Enum, ForeignKey, Integer, Numeric, String, Text

from app.database.connection import Base
from app.models.enums import ActorRole, TransferEventType


class TransferEvent(Base):
    __tablename__ = "transfer_event"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transfer_id = Column(Integer, ForeignKey("transfer.id"), nullable=False, index=True)
    event_type = Column(Enum(TransferEventType, native_enum=False, length=20), nullable=False)
    actor_role = Column(Enum(ActorRole, native_enum=False, length=20), nullable=False)
    employee_profile_id = Column(Integer, ForeignKey("employee_profile.id"), nullable=True)
    employee_name = Column(String(255), nullable=False)
    quantity = Column(Numeric(12, 3), nullable=True)
    comment = Column(Text, nullable=True)
    photo_path = Column(String(500), nullable=True)
    created_at = Column(BigInteger, nullable=False, index=True)
