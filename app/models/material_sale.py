from sqlalchemy import BigInteger, Column, ForeignKey, Integer, Numeric, String, Text

from app.database.connection import Base


class MaterialSale(Base):
    __tablename__ = "material_sale"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scrapeyard_id = Column(Integer, ForeignKey("scrapeyard.id"), nullable=False, index=True)
    item_code = Column(String(20), nullable=False, index=True)
    item_name = Column(String(500), nullable=False)
    uom = Column(String(10), nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendor.id"), nullable=False)
    vehicle_number = Column(String(50), nullable=False)
    quantity_sold = Column(Numeric(12, 3), nullable=False)
    total_weight_kg = Column(Numeric(12, 3), nullable=True)
    amount_inr = Column(Numeric(14, 2), nullable=True)
    status = Column(String(20), nullable=False, index=True)
    recorded_by = Column(Integer, ForeignKey("employee_profile.id"), nullable=False)
    recorded_at = Column(BigInteger, nullable=False, index=True)
    reviewed_by = Column(Integer, ForeignKey("employee_profile.id"), nullable=True)
    reviewed_by_admin_id = Column(Integer, ForeignKey("admin_user.id"), nullable=True)
    reviewed_at = Column(BigInteger, nullable=True)
    rejection_comment = Column(Text, nullable=True)
    transfer_id = Column(Integer, ForeignKey("transfer.id"), nullable=True)
