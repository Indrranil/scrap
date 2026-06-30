from sqlalchemy import BigInteger, Column, ForeignKey, Integer, Numeric, String

from app.database.connection import Base


class InventoryMovement(Base):
    __tablename__ = "inventory_movement"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scrapeyard_id = Column(Integer, ForeignKey("scrapeyard.id"), nullable=False, index=True)
    item_code = Column(String(20), nullable=False)
    movement_type = Column(String(30), nullable=False)
    quantity_delta = Column(Numeric(12, 3), nullable=False)
    reference_type = Column(String(30), nullable=True)
    reference_id = Column(Integer, nullable=True)
    created_at = Column(BigInteger, nullable=False)
