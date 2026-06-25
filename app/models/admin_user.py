from sqlalchemy import BigInteger, Boolean, Column, Integer, String

from app.database.connection import Base


class AdminUser(Base):
    __tablename__ = "admin_user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(BigInteger, nullable=False)
