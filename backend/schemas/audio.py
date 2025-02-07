from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AudioBase(BaseModel):
    filename: str

class AudioCreate(AudioBase):
    original_waveform: bytes
    waveform: bytes
    start_timestamp: int
    speech_duration: float
    total_duration: float

    class Config:
        arbitrary_types_allowed = True

class AudioUpdate(AudioBase):
    pass

class Audio(AudioBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
