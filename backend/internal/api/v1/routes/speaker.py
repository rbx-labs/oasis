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
    try:
        speakers = crud_speaker.get_all_profiles(db)
        return speakers
    except Exception as e:
        logger.error(f"Error retrieving speakers: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving speakers"
        )

@router.delete("/{speaker_id}", status_code=204)
async def delete_speaker(
    speaker_id: str,
    db: Session = Depends(session.get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Delete a speaker by ID
    """
    try:
        if not crud_speaker.delete_profile(db, speaker_id):
            raise HTTPException(status_code=404, detail="Speaker not found")
    except Exception as e:
        logger.error(f"Error deleting speaker {speaker_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while deleting speaker"
        )

@router.post("/reset", status_code=204)
async def reset_speakers(
    db: Session = Depends(session.get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Reset all speakers in the database
    """
    try:
        crud_speaker.reset_all_profiles(db)
    except Exception as e:
        logger.error(f"Error resetting speakers: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while resetting speakers"
        )
