from sqlalchemy import BigInteger, Boolean, Column, Integer, String

from app.database.connection import Base


class ItemMaster(Base):
    __tablename__ = "item_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plu_code = Column(String(20), unique=True, nullable=False, index=True)
    item_code = Column(String(20), unique=True, nullable=True, index=True)
    name = Column(String(500), nullable=False, index=True)
    uom = Column(String(10), nullable=False)
    is_shreddable = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)
