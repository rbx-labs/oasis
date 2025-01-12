from typing import List, Optional
from sqlalchemy.orm import Session
from app.crud.crud_base import CRUDBase
from app.models.speaker_clips import SpeakerClip
from app.schemas.audio import SpeakerClipCreate, SpeakerClip as SpeakerClipSchema

class CRUDSpeakerClip(CRUDBase[SpeakerClip, SpeakerClipCreate, SpeakerClipSchema]):
    def get_by_audio_id(self, db: Session, *, audio_id: int) -> List[SpeakerClip]:
        return db.query(self.model).filter(SpeakerClip.audio_id == audio_id).all()
    
    def get_by_profile_id(self, db: Session, *, profile_id: str) -> Optional[SpeakerClip]:
        return db.query(self.model).filter(SpeakerClip.profile_id == profile_id).first()

crud_speaker_clips = CRUDSpeakerClip(SpeakerClip) 