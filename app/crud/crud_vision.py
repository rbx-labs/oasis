from typing import List, Optional
from sqlalchemy.orm import Session
from app.crud.crud_base import CRUDBase
from app.models.vision import Vision
from app.schemas.vision import VisionCreate, VisionUpdate

class CRUDVision(CRUDBase[Vision, VisionCreate, VisionUpdate]):
    pass

crud_vision = CRUDVision(Vision)