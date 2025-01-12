from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class Diarization(Base):
    __tablename__ = "diarizations"

    id = Column(Integer, primary_key=True, index=True)
    audio_id = Column(Integer, ForeignKey("audios.id", ondelete="CASCADE"), nullable=False)
    speaker = Column(String, nullable=False)
    text = Column(String)
    start_time = Column(Float)
    end_time = Column(Float)
    confidence = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    audio = relationship("Audio", back_populates="diarizations") 