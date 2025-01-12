from sqlalchemy import Column, Integer, String, LargeBinary, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class SpeakerClip(Base):
    __tablename__ = "speaker_clips"

    id = Column(Integer, primary_key=True, index=True)
    audio_id = Column(Integer, ForeignKey("audios.id"))
    speaker = Column(String)
    waveform = Column(LargeBinary)
    profile_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    audio = relationship("Audio", back_populates="speaker_clips") 