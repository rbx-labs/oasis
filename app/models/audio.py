from sqlalchemy import Column, Float, Integer, String, LargeBinary, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class Audio(Base):
    __tablename__ = "audios"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    waveform = Column(LargeBinary)
    start_timestamp = Column(Integer)
    speech_duration = Column(Float)
    total_duration = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    transcriptions = relationship("Transcription", back_populates="audio")
    diarization_segments = relationship("DiarizationSegment", back_populates="audio")
    speaker_clips = relationship("SpeakerClip", back_populates="audio")
    conversations = relationship("Conversation", back_populates="audio")
    gladia_responses = relationship("GladiaResponse", back_populates="audio")
    voice_segments = relationship("VoiceSegment", back_populates="audio", cascade="all, delete")