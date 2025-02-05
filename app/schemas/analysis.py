from pydantic import BaseModel
from datetime import datetime

class AnalysisRequest(BaseModel):
    pass

class Analysis(BaseModel):
    audio_id: int
    text: str
    analysis: str
    created_at: datetime

    class Config:
        from_attributes = True 