from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    audio_id = Column(Integer, ForeignKey("audios.id"))
    speaker = Column(String, nullable=False)  # Speaker identifier
    content = Column(String, nullable=False)  # Conversation content
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    audio = relationship("Audio", back_populates="conversations") 