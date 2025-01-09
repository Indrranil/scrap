from sqlalchemy import Column, Integer, String, BigInteger
from database.connection import Base

class Pipeline(Base):
   __tablename__ = "pipeline"
   id = Column(Integer, primary_key=True, index=True)
   name = Column(String(255))
   created_at = Column(BigInteger)
   is_usable = Column(Integer)