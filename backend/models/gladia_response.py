from sqlalchemy import Column, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.base import Base

class GladiaResponse(Base):
    __tablename__ = "gladia_responses"

    id = Column(Integer, primary_key=True, index=True)
    voice_segment_id = Column(Integer, ForeignKey("voice_segments.id"), nullable=False)
    response_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    voice_segment = relationship("VoiceSegment", back_populates="gladia_response") 