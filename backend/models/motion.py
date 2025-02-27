from sqlalchemy import Column, Integer, DateTime, LargeBinary
from sqlalchemy.sql import func
from db.base import Base

class Motion(Base):
    __tablename__ = "motion"

    id = Column(Integer, primary_key=True, index=True)
    motion_data = Column(LargeBinary)
    timestamp = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 