from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey
from database.connection import Base

class Application(Base):
   __tablename__ = "application"
   id = Column(Integer, primary_key=True, index=True)
   name = Column(String(255))
   is_running = Column(Integer)
   pipeline_id = Column(Integer, ForeignKey('pipeline.id'))
   created_at = Column(BigInteger)
   is_usable = Column(Integer)