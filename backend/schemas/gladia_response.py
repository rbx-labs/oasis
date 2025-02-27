from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime

class GladiaResponseBase(BaseModel):
    response_data: Dict[str, Any]

class GladiaResponseCreate(GladiaResponseBase):
    voice_segment_id: int

class GladiaResponseUpdate(GladiaResponseBase):
    pass

class GladiaResponse(GladiaResponseBase):
    id: int
    voice_segment_id: int
    created_at: datetime

    class Config:
        from_attributes = True