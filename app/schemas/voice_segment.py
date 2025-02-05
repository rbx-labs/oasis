from pydantic import BaseModel

class VoiceSegmentBase(BaseModel):
    pass

class VoiceSegmentCreate(VoiceSegmentBase):
    waveform: bytes
    audio_id: int
    segment_id: int
    start_time: int
    end_time: int
    duration: float
    
    class Config:
        arbitrary_types_allowed = True

class VoiceSegmentUpdate(VoiceSegmentBase):
    pass

class VoiceSegment(VoiceSegmentBase):
    class Config:
        from_attributes = True
