from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Base Audio schema without transcription reference
class AudioBase(BaseModel):
    id: int
    filename: str
    created_at: datetime

    class Config:
        from_attributes = True

class TranscriptionBase(BaseModel):
    text: str
    audio_id: int

class TranscriptionCreate(TranscriptionBase):
    pass

class TranscriptionUpdate(TranscriptionBase):
    text: Optional[str] = None
    audio_id: Optional[int] = None

class Transcription(TranscriptionBase):
    id: int
    created_at: datetime
    audio: AudioBase  # Use AudioBase instead of Audio to avoid circular reference

    class Config:
        from_attributes = True