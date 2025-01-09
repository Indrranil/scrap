from sqlalchemy import Column, Integer, String, BigInteger, Enum
from database.connection import Base

class ApplicationStatusLog(Base):
    __tablename__ = "application_status_log"
    id = Column(Integer, primary_key=True, index=True)
    application_container_id = Column(String(255))
    value = Column(Enum('start', 'starting', 'started', 'idle', 'running', 
                       'kill', 'killing', 'killed', 'stop', 'stopping', 
                       'stopped', 'error'))
    created_at = Column(BigInteger)
