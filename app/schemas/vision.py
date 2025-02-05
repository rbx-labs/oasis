from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from enum import IntEnum

class VisionType(IntEnum):
    RAW = 0
    EMBEDDINGS = 1

class VisionBase(BaseModel):
    image_data: bytes
    timestamp: int
    type: VisionType = VisionType.RAW  # Default to RAW (0)

class VisionCreate(VisionBase):
    pass

class VisionUpdate(VisionBase):
    pass

class Vision(VisionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 