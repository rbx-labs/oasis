from sqlalchemy import Column, Float, Integer, String, LargeBinary, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.base import Base
from models.voice_segment import VoiceSegment

class Audio(Base):
    __tablename__ = "audios"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    waveform = Column(LargeBinary)
    original_waveform = Column(LargeBinary)
    start_timestamp = Column(Integer)
    speech_duration = Column(Float)
    total_duration = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    voice_segments = relationship("VoiceSegment", back_populates="audio", cascade="all, delete")