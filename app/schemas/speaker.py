from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SpeakerBase(BaseModel):
    profile_id: str
    speaker_label: Optional[str] = None

class SpeakerCreate(SpeakerBase):
    pass

class SpeakerUpdate(BaseModel):
    profile_id: Optional[str] = None
    speaker_label: Optional[str] = None

class Speaker(SpeakerBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 