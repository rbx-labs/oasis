from sqlalchemy import Column, Integer, DateTime, LargeBinary
from sqlalchemy.sql import func
from db.base import Base

class Vision(Base):
    __tablename__ = "vision"

    id = Column(Integer, primary_key=True, index=True)
    image_data = Column(LargeBinary)
    timestamp = Column(Integer)
    type = Column(Integer, default=0)  # 0 for raw, 1 for embeddings
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 