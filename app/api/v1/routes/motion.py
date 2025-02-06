from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api import deps
from app.core.security import get_api_key
from app.crud.crud_motion import crud_motion
from app.schemas.motion import Motion, MotionCreate
import logging
import base64
import time
from pydantic import BaseModel, field_validator

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter()

class MotionUploadRequest(BaseModel):
    motion_data: str
    timestamp: int

    @field_validator('motion_data')
    @classmethod
    def validate_base64(cls, v):
        try:
            # Try to decode the base64 string
            base64.b64decode(v)
            return v
        except Exception:
            raise ValueError('Invalid base64 string')

    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v):
        current_time = int(time.time())
        # Check if timestamp is not from the future and not too old (e.g., max 1 year old)
        if v > current_time:
            raise ValueError('Timestamp cannot be in the future')
        if v < current_time - (365 * 24 * 60 * 60):  # 1 year in seconds
            raise ValueError('Timestamp is too old')
        return v

@router.post("/upload", response_model=Motion)
async def upload_motion(
    *,
    _api_key: str = Depends(get_api_key),
    db: Session = Depends(deps.get_db),
    request_data: MotionUploadRequest
):
    """
    Upload motion data and process it
    
    Request body:
    - motion_data: Raw bytes of the motion data (base64 encoded)
    - timestamp: Unix timestamp for the motion data
    """
    logger.info(f"Uploading motion data: timestamp: {request_data.timestamp}, size: {len(request_data.motion_data)} bytes")
    
    motion_in = MotionCreate(
        motion_data=request_data.motion_data,
        timestamp=request_data.timestamp,
    )

    motion = crud_motion.create(db, obj_in=motion_in)
    
    return motion 