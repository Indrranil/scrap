from sqlalchemy import BigInteger, Boolean, Column, Integer, String

from app.database.connection import Base


class Vendor(Base):
    __tablename__ = "vendor"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(BigInteger, nullable=False)
