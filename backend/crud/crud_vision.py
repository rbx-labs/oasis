from typing import List, Optional
from sqlalchemy.orm import Session
from crud.crud_base import CRUDBase
from models.vision import Vision
from schemas.vision import VisionCreate, VisionUpdate

class CRUDVision(CRUDBase[Vision, VisionCreate, VisionUpdate]):
    pass

crud_vision = CRUDVision(Vision)