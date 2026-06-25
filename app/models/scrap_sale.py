from sqlalchemy import BigInteger, Column, ForeignKey, Integer, Numeric, String, Text

from app.database.connection import Base


class ScrapSale(Base):
    __tablename__ = "scrap_sale"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transfer_id = Column(Integer, ForeignKey("transfer.id"), nullable=False, index=True)
    plant_id = Column(Integer, ForeignKey("plant.id"), nullable=False, index=True)
    quantity_kg = Column(Numeric(12, 3), nullable=True, default=0)
    quantity_ea = Column(Numeric(12, 3), nullable=True, default=0)
    amount_inr = Column(Numeric(14, 2), nullable=False)
    sold_at = Column(BigInteger, nullable=False)
    notes = Column(Text, nullable=True)
