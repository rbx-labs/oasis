from typing import Any, Dict, Optional, Union, List

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.vad_segment import VadSegment
from app.schemas.vad_segment import VadSegmentCreate, VadSegmentUpdate

class CRUDVadSegment(CRUDBase[VadSegment, VadSegmentCreate, VadSegmentUpdate]):
    def get_by_audio_id(self, db: Session, *, audio_id: int) -> List[VadSegment]:
        return db.query(self.model).filter(VadSegment.audio_id == audio_id).all()

crud_vad_segments = CRUDVadSegment(VadSegment)
