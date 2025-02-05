from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from enum import IntEnum

class MotionBase(BaseModel):
    motion_data: bytes
    timestamp: int

class MotionCreate(MotionBase):
    pass

class MotionUpdate(MotionBase):
    pass

class Motion(MotionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 