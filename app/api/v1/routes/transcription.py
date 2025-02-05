from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api import deps
from app.schemas.transcription import Transcription
from app.crud.crud_transcription import crud_transcription
from app.core.security import get_api_key
from app.models.transcription import Transcription as TranscriptionModel
from app.schemas.analysis import AnalysisRequest, Analysis
from app.utils.openai_processing import OpenAIProcessor
import logging
from datetime import datetime
from app.models.audio import Audio as AudioModel
from app.models.voice_segment import VoiceSegment
from app.models.gladia_response import GladiaResponse

# Configure logging
logger = logging.getLogger(__name__)
openai_processor = OpenAIProcessor()

router = APIRouter()

@router.get("/all", response_model=List[Transcription])
async def read_transcriptions(
    _api_key: str = Depends(get_api_key),
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve all transcriptions
    """
    transcriptions = crud_transcription.get_multi(db, skip=skip, limit=limit)
    logger.info(f"Retrieved {len(transcriptions)} transcriptions")
    return transcriptions

@router.get("/latest", response_model=Transcription)
async def get_latest_transcription(
    _api_key: str = Depends(get_api_key),
    db: Session = Depends(deps.get_db)
):
    """
    Get the most recent transcription
    """
    transcription = db.query(TranscriptionModel).order_by(TranscriptionModel.created_at.desc()).first()
    if not transcription:
        raise HTTPException(
            status_code=404,
            detail="No transcriptions found"
        )
    logger.info(f"Retrieved latest transcription (ID: {transcription.id})")
    return transcription

@router.get("/{transcription_id}", response_model=Transcription)
async def get_transcription(
    transcription_id: int,
    _api_key: str = Depends(get_api_key),
    db: Session = Depends(deps.get_db)
):
    """
    Get a specific transcription by ID
    """
    transcription = crud_transcription.get(db, id=transcription_id)
    if not transcription:
        raise HTTPException(
            status_code=404,
            detail=f"Transcription with ID {transcription_id} not found"
        )
    logger.info(f"Retrieved transcription {transcription_id}")
    return transcription 

@router.get("/latest/analyze", response_model=Analysis)
async def analyze_latest_transcription(
    _api_key: str = Depends(get_api_key),
    db: Session = Depends(deps.get_db)
):
    """
    Analyze the latest transcription using OpenAI by formatting voice segments with timestamps and speakers
    """
    # Get the latest audio
    latest_audio = db.query(AudioModel).order_by(AudioModel.created_at.desc()).first()
    if not latest_audio:
        raise HTTPException(
            status_code=404,
            detail="No audio recordings found"
        )

    # Get all voice segments and gladia responses for this audio, ordered by timestamp
    voice_segments = (
        db.query(VoiceSegment, GladiaResponse)
        .join(GladiaResponse, VoiceSegment.id == GladiaResponse.voice_segment_id)
        .filter(VoiceSegment.audio_id == latest_audio.id)
        .order_by(VoiceSegment.start_time)
        .all()
    )

    if not voice_segments:
        raise HTTPException(
            status_code=404,
            detail="No voice segments found for the latest audio"
        )

    # Format the conversation text
    formatted_text = []
    for segment, gladia_response in voice_segments:
        # Extract speaker and text from response_data
        response_data = gladia_response.response_data
        if response_data and "result" in response_data:
            utterances = response_data["result"]["transcription"]["utterances"]
            for utterance in utterances:
                speaker_id = utterance.get("speaker")
                text = utterance.get("text", "")
                start = utterance.get("start", 0)
                timestamp = datetime.fromtimestamp(segment.start_time / 1000 + start).strftime("%-m/%-d %-I:%M:%S%p")
                formatted_text.append(f"{timestamp} [Speaker_{speaker_id}]: {text}")
    formatted_text = "\n".join(formatted_text)
    
    try:
        analysis = openai_processor.analyze_text(formatted_text)
        logger.info(f"Generated analysis for audio {latest_audio.id}")
        
        return {
            "audio_id": latest_audio.id,
            "text": formatted_text,
            "analysis": analysis["response"],
            "created_at": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to analyze conversation"
        ) 