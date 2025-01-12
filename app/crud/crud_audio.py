from typing import Optional
from sqlalchemy.orm import Session
from app.crud.crud_base import CRUDBase
from app.models.audio import Audio
from app.schemas.audio import AudioCreate, AudioUpdate

class CRUDAudio(CRUDBase[Audio, AudioCreate, AudioUpdate]):
    def get_by_filename(self, db: Session, *, filename: str) -> Optional[Audio]:
        return db.query(Audio).filter(Audio.filename == filename).first()

crud_audio = CRUDAudio(Audio) 