from sqlalchemy import Column, ForeignKey, Integer, Numeric, UniqueConstraint

from app.database.connection import Base


class VendorItem(Base):
    __tablename__ = "vendor_item"
    __table_args__ = (
        UniqueConstraint("vendor_id", "item_id", name="uq_vendor_item"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    vendor_id = Column(Integer, ForeignKey("vendor.id"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("item_master.id"), nullable=False, index=True)
    rate_inr = Column(Numeric(12, 2), nullable=False)
