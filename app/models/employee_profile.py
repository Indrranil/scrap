from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, Integer, String

from app.database.connection import Base


class EmployeeProfile(Base):
    __tablename__ = "employee_profile"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plant_id = Column(Integer, ForeignKey("plant.id"), nullable=True, index=True)
    scrapeyard_id = Column(Integer, ForeignKey("scrapeyard.id"), nullable=True, index=True)
    gso_id = Column(Integer, ForeignKey("gso.id"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(BigInteger, nullable=False)
