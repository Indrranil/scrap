from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey
from database.connection import Base

class ApplicationSession(Base):
   __tablename__ = "application_session"
   id = Column(Integer, primary_key=True, index=True)
   application_id = Column(Integer, ForeignKey('application.id'))
   name = Column(String(255))
   created_by = Column(Integer)
   created_at = Column(BigInteger)
   ended_at = Column(BigInteger)
   is_usable = Column(Integer)