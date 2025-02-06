from typing import List, Optional
from sqlalchemy.orm import Session
from crud.crud_base import CRUDBase
from models.motion import Motion
from schemas.motion import MotionCreate, MotionUpdate

class CRUDMotion(CRUDBase[Motion, MotionCreate, MotionUpdate]):
    pass

crud_motion = CRUDMotion(Motion) 