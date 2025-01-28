from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class VadSegmentBase(BaseModel):
    start_time: float = Field(..., description="Start time of the segment in seconds")
    end_time: float = Field(..., description="End time of the segment in seconds")

class VadSegmentCreate(VadSegmentBase):
    audio_id: int
    segment_waveform: bytes

    class Config:
        arbitrary_types_allowed = True

class VadSegmentUpdate(VadSegmentBase):
    pass

class VadSegment(VadSegmentBase):
    id: int
    audio_id: int
    created_at: datetime

    class Config:
        from_attributes = True
