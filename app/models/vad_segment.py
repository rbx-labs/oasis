from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class VadSegment(Base):
    __tablename__ = "vad_segments"

    id = Column(Integer, primary_key=True, index=True)
    audio_id = Column(Integer, ForeignKey("audios.id"))
    start_time = Column(Float)
    end_time = Column(Float)
    segment_waveform = Column(LargeBinary)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    audio = relationship("Audio", back_populates="vad_segments")
