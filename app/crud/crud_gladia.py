from typing import List, Optional
from sqlalchemy.orm import Session
from app.crud.crud_base import CRUDBase
from app.models.gladia_response import GladiaResponse
from app.schemas.gladia_response import GladiaResponseCreate, GladiaResponse as GladiaResponseSchema

class CRUDGladia(CRUDBase[GladiaResponse, GladiaResponseCreate, GladiaResponseSchema]):
    def get_by_audio_id(self, db: Session, *, audio_id: int) -> List[GladiaResponse]:
        return db.query(self.model).filter(GladiaResponse.audio_id == audio_id).all()

crud_gladia = CRUDGladia(GladiaResponse) 