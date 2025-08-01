from sqlalchemy import BigInteger, Column, ForeignKey, Integer, String

from app.database.connection import Base


class Pipeline(Base):
    __tablename__ = "pipeline"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255))
    is_running = Column(Integer)
    application_id = Column(Integer, ForeignKey("application.id"))
    created_at = Column(BigInteger)
    is_usable = Column(Integer)
