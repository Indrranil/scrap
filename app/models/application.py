from sqlalchemy import BigInteger, Column, Integer, String

from app.database.connection import Base


class Application(Base):
    __tablename__ = "application"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(BigInteger)
    is_usable = Column(Integer)

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __setattr__(self, name, value):
        # Allow setting attributes during SQLAlchemy operations
        if name in self.__mapper__.attrs:
            object.__setattr__(self, name, value)
        else:
            super().__setattr__(name, value)
