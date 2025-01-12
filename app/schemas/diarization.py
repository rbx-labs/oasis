from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DiarizationBase(BaseModel):
    speaker: str
    text: Optional[str] = None
    start_time: float
    end_time: float
    confidence: Optional[float] = None

class DiarizationCreate(DiarizationBase):
    audio_id: int

class Diarization(DiarizationBase):
    id: int
    audio_id: int
    created_at: datetime

    class Config:
        from_attributes = True 