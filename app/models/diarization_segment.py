from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class DiarizationSegment(Base):
    __tablename__ = "diarization_segments"

    id = Column(Integer, primary_key=True, index=True)
    audio_id = Column(Integer, ForeignKey("audios.id"))
    speaker = Column(String)  # e.g., "Speaker 1"
    start_time = Column(Float)
    end_time = Column(Float)
    confidence = Column(Float)
    raw_response = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)

    # Relationships
    audio = relationship("Audio", back_populates="diarization_segments") 