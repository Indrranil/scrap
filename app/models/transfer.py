from sqlalchemy import BigInteger, Boolean, Column, Enum, ForeignKey, Integer, Numeric, String, Text

from app.database.connection import Base
from app.models.enums import DispatchMethod, MaterialState, TransferStatus


class Transfer(Base):
    __tablename__ = "transfer"

    id = Column(Integer, primary_key=True, autoincrement=True)
    qr_raw = Column(String(2000), nullable=True)
    qr_number = Column(String(255), unique=True, nullable=False, index=True)
    shopfloor_plant_id = Column(Integer, ForeignKey("plant.id"), nullable=False, index=True)
    scrapeyard_id = Column(Integer, ForeignKey("scrapeyard.id"), nullable=True, index=True)
    item_master_id = Column(Integer, ForeignKey("item_master.id"), nullable=True, index=True)
    plu_code = Column(String(20), nullable=True, index=True)
    item_code = Column(String(100), nullable=False, index=True)
    item_name = Column(String(500), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    uom = Column(String(10), nullable=False)
    quantity_sent = Column(Numeric(12, 3), nullable=False)
    quantity_received = Column(Numeric(12, 3), nullable=True)
    location = Column(Integer, nullable=True)
    net_weight = Column(Numeric(12, 3), nullable=True)
    tare_weight = Column(Numeric(12, 3), nullable=True)
    gross_weight = Column(Numeric(12, 3), nullable=True)
    dispatch_method = Column(
        Enum(DispatchMethod, native_enum=False, length=10),
        nullable=False,
        default=DispatchMethod.QR,
    )
    material_state = Column(
        Enum(MaterialState, native_enum=False, length=20),
        nullable=False,
        default=MaterialState.NOT_SHREDDED,
    )
    is_p_item = Column(Boolean, nullable=False, default=False)
    status = Column(
        Enum(TransferStatus, native_enum=False, length=20),
        nullable=False,
        default=TransferStatus.PENDING,
        index=True,
    )
    dispatched_by = Column(Integer, ForeignKey("employee_profile.id"), nullable=True)
    dispatched_at = Column(BigInteger, nullable=True)
    processed_by = Column(Integer, ForeignKey("employee_profile.id"), nullable=True)
    processed_at = Column(BigInteger, nullable=True)
    acknowledged_by = Column(Integer, ForeignKey("employee_profile.id"), nullable=True)
    acknowledged_at = Column(BigInteger, nullable=True)
    gso_approved_by = Column(Integer, ForeignKey("employee_profile.id"), nullable=True)
    gso_approved_at = Column(BigInteger, nullable=True)
    gso_auto_approved = Column(Boolean, nullable=False, default=False)
    gso_rejected_by = Column(Integer, ForeignKey("employee_profile.id"), nullable=True)
    gso_rejected_at = Column(BigInteger, nullable=True)
    gso_rejection_reason = Column(Text, nullable=True)
