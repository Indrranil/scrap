from sqlalchemy import BigInteger, Boolean, Column, Integer, String

from app.database.connection import Base


class Vendor(Base):
    __tablename__ = "vendor"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    vendor_code = Column(String(50), unique=True, nullable=True, index=True)
    email = Column(String(255), nullable=True)
    contact_person = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(String(500), nullable=True)
    gst_number = Column(String(50), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=True)
