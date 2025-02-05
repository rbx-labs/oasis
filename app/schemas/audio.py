from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

# Base Transcription schema without audio reference
class TranscriptionBase(BaseModel):
    id: int
    text: str
    created_at: datetime

    class Config:
        from_attributes = True

class AudioBase(BaseModel):
    filename: str

class AudioCreate(AudioBase):
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
    transcription: Optional[TranscriptionBase] = None  # Use TranscriptionBase to avoid circular reference

    class Config:
        from_attributes = True

class DiarizationSegmentBase(BaseModel):
    speaker: str
    start_time: float
    end_time: float
    confidence: float
    raw_response: Dict[str, Any]

class DiarizationSegmentCreate(DiarizationSegmentBase):
    audio_id: int

class DiarizationSegment(DiarizationSegmentBase):
    id: int
    audio_id: int
    
    class Config:
        from_attributes = True

class SpeakerClipBase(BaseModel):
    speaker: str
    profile_id: Optional[str] = None

class SpeakerClipCreate(SpeakerClipBase):
    audio_id: int
    waveform: bytes

class SpeakerClip(SpeakerClipBase):
    id: int
    audio_id: int
    
    class Config:
        from_attributes = True

class ConversationBase(BaseModel):
    audio_id: int
    speaker: str
    content: str

class ConversationCreate(ConversationBase):
    pass

class Conversation(ConversationBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
