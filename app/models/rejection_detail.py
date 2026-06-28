from sqlalchemy import Column, Enum, ForeignKey, Integer, Numeric, String, Text

from app.database.connection import Base
from app.models.enums import RejectionReasonType


class RejectionDetail(Base):
    __tablename__ = "rejection_detail"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transfer_id = Column(Integer, ForeignKey("transfer.id"), unique=True, nullable=False)
    reason_type = Column(
        Enum(
            RejectionReasonType,
            native_enum=False,
            length=30,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
    )
    qty_received = Column(Numeric(12, 3), nullable=True)
    material_received_name = Column(String(500), nullable=True)
    comment = Column(Text, nullable=True)
