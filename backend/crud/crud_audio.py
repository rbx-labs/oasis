from typing import Optional
from sqlalchemy.orm import Session
from crud.crud_base import CRUDBase
from models.audio import Audio
from schemas.audio import AudioCreate, AudioUpdate

class CRUDAudio(CRUDBase[Audio, AudioCreate, AudioUpdate]):
    def get_by_filename(self, db: Session, *, filename: str) -> Optional[Audio]:
        return db.query(Audio).filter(Audio.filename == filename).first()

crud_audio = CRUDAudio(Audio) 