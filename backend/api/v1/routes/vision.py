from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import session
from core.security import get_api_key
from crud.crud_vision import crud_vision
from schemas.vision import Vision, VisionCreate, VisionType
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

class ImageUploadRequest(BaseModel):
    image_data: str
    timestamp: int
    type: VisionType

    @field_validator('image_data')
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

@router.post("/upload", response_model=Vision)
async def upload_image(
    *,
    _api_key: str = Depends(get_api_key),
    db: Session = Depends(session.get_db),
    request_data: ImageUploadRequest
):
    """
    Upload image data and process it
    
    Request body:
    - image_data: Raw bytes of the image (base64 encoded)
    - timestamp: Unix timestamp for the image file
    - type: Integer (0 for raw, 1 for embeddings), defaults to 0
    """
    logger.info(f"Uploading image data: timestamp: {request_data.timestamp}, size: {len(request_data.image_data)} bytes, type: {request_data.type}")
    
    vision_in = VisionCreate(
        image_data=request_data.image_data,
        timestamp=request_data.timestamp,
        type=request_data.type
    )

    vision = crud_vision.create(db, obj_in=vision_in)
    
    return vision
