from sqlalchemy import BigInteger, Column, ForeignKey, Integer, Numeric, String

from app.database.connection import Base


class MaterialInventory(Base):
    __tablename__ = "material_inventory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scrapeyard_id = Column(Integer, ForeignKey("scrapeyard.id"), nullable=False, index=True)
    item_code = Column(String(20), nullable=False, index=True)
    item_name = Column(String(500), nullable=False)
    uom = Column(String(10), nullable=False)
    quantity_available = Column(Numeric(12, 3), nullable=False)
    updated_at = Column(BigInteger, nullable=False)
