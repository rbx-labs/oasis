from typing import List, Optional
from sqlalchemy.orm import Session
from app.crud.crud_base import CRUDBase
from app.models.motion import Motion
from app.schemas.motion import MotionCreate, MotionUpdate

class CRUDMotion(CRUDBase[Motion, MotionCreate, MotionUpdate]):
    pass

crud_motion = CRUDMotion(Motion) 