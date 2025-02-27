from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from db.base import Base

class Speaker(Base):
    __tablename__ = "speakers"
    
    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(String, unique=True, index=True)
    speaker_label = Column(String, nullable=True)  # e.g., "Speaker_0", "Speaker_1"
    context = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 