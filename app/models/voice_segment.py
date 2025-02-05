from sqlalchemy import Column, Float, ForeignKey, Integer, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class VoiceSegment(Base):
    __tablename__ = "voice_segments"

    id = Column(Integer, primary_key=True, index=True)
    audio_id = Column(Integer, ForeignKey("audios.id"), nullable=False)
    segment_id = Column(Integer, nullable=False)
    waveform = Column(LargeBinary)
    start_time = Column(Integer)
    end_time = Column(Integer)
    duration = Column(Float)

    # Relationships
    audio = relationship("Audio", back_populates="voice_segments")