from typing import List, Optional
from sqlalchemy.orm import Session
from app.crud.crud_base import CRUDBase
from app.models.diarization_segment import DiarizationSegment
from app.schemas.audio import DiarizationSegmentCreate, DiarizationSegment as DiarizationSegmentSchema

class CRUDDiarization(CRUDBase[DiarizationSegment, DiarizationSegmentCreate, DiarizationSegmentSchema]):
    def get_by_audio_id(self, db: Session, *, audio_id: int) -> List[DiarizationSegment]:
        return db.query(self.model).filter(DiarizationSegment.audio_id == audio_id).all()

crud_diarization = CRUDDiarization(DiarizationSegment) 