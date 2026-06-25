from sqlalchemy import BigInteger, Boolean, Column, Enum, ForeignKey, Integer, String

from app.database.connection import Base
from app.models.enums import AppRole


class Plant(Base):
    __tablename__ = "plant"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), nullable=True)
    name = Column(String(255), nullable=False)
    login_id = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    app_role = Column(Enum(AppRole, native_enum=False, length=20), nullable=False)
    address = Column(String(500), nullable=True)
    linked_scrapeyard_plant_id = Column(Integer, ForeignKey("plant.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(BigInteger, nullable=False)
