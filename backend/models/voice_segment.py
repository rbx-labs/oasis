from sqlalchemy import Column, Float, ForeignKey, Integer, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.base import Base
from .gladia_response import GladiaResponse

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
    gladia_response = relationship("GladiaResponse", back_populates="voice_segment", cascade="all, delete")