from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from crud.crud_speaker import crud_speaker
from db import session
from core.security import get_api_key
import logging
from schemas.speaker import Speaker

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("", response_model=list[Speaker])
async def get_all_speakers(
    db: Session = Depends(session.get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Get all speakers from the database
    """
    print("Getting all speakers")
    try:
        speakers = crud_speaker.get_all_profiles(db)
        return speakers
    except Exception as e:
        logger.error(f"Error retrieving speakers: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving speakers"
        )
