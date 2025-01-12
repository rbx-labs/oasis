from sqlalchemy import Column, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    audio_id = Column(Integer, ForeignKey("audios.id"))
    conversation_data = Column(JSON)  # Final mapped and formatted conversation data
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    audio = relationship("Audio", back_populates="conversations") 