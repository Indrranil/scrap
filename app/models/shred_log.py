from sqlalchemy import BigInteger, Column, ForeignKey, Integer, Numeric, String

from app.database.connection import Base


class ShredLog(Base):
    __tablename__ = "shred_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transfer_id = Column(Integer, ForeignKey("transfer.id"), nullable=False, unique=True, index=True)
    scrapeyard_id = Column(Integer, ForeignKey("scrapeyard.id"), nullable=False, index=True)
    input_plu_code = Column(String(20), nullable=False)
    input_name = Column(String(500), nullable=False)
    output_item_code = Column(String(20), nullable=False, index=True)
    output_name = Column(String(500), nullable=False)
    quantity_pre_shred = Column(Numeric(12, 3), nullable=False)
    quantity_post_shred = Column(Numeric(12, 3), nullable=False)
    shredded_by = Column(Integer, ForeignKey("employee_profile.id"), nullable=False)
    shredded_at = Column(BigInteger, nullable=False, index=True)
