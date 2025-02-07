from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from db import session
from schemas.audio import (
    Audio, AudioCreate
)
from schemas.voice_segment import VoiceSegmentCreate
from crud.crud_audio import crud_audio
from crud.crud_voice_segment import crud_voice_segment
from core.security import get_api_key
import logging
from utils.audio_processor import AudioProcessor
from utils.gladia_processor import GladiaProcessor
from utils.whisper_processor import WhisperProcessor
from utils.azure_speech_processor import AzureSpeechProcessor

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize processors as module-level singletons
audio_processor = AudioProcessor()
gladia_processor = GladiaProcessor()
whisper_processor = WhisperProcessor()
azure_speech_processor = AzureSpeechProcessor()
router = APIRouter()

@router.post("/upload", response_model=Audio)
async def upload_audio(
    *,
    _api_key: str = Depends(get_api_key),
    db: Session = Depends(session.get_db),
    file: UploadFile = File(...),
    start_timestamp: int = Form(...)
):
    """
    Upload audio file and process waveform using Silero VAD
    
    Parameters:
    - file: Audio file to upload
    - start_timestamp: Unix timestamp for the audio file
    """
    try:
        existing_audio = crud_audio.get_by_filename(db, filename=file.filename)
        if existing_audio:
            crud_audio.remove(db, id=existing_audio.id)
            
        await file.seek(0)
        original_waveform = await file.read()
        logger.info(f"Uploading file: {file.filename}, start_timestamp: {start_timestamp}, size: {len(original_waveform)} bytes")
        
        waveform, segments, speech_ratio, total_duration, speech_duration = audio_processor.process_audio(original_waveform)
        logger.info(f"Processed audio file. Speech ratio: {speech_ratio:.2%}")

        audio_in = AudioCreate(
            filename=file.filename,
            original_waveform=original_waveform,
            waveform=waveform,
            start_timestamp=start_timestamp,
            total_duration=total_duration,
            speech_duration=speech_duration
        )

        audio = crud_audio.create(db, obj_in=audio_in)
        
        voice_segments = []
        for segment in segments:
            voice_segment_in = VoiceSegmentCreate(
                audio_id=audio.id,
                segment_id=segment["segment_id"],
                waveform=segment["buffer"],
                start_time=segment["start_ts"] + start_timestamp,
                end_time=segment["end_ts"] + start_timestamp,
                duration=(segment["end_ts"] - segment["start_ts"]) / 1000
            )
            voice_segment = crud_voice_segment.create(db, obj_in=voice_segment_in)
            voice_segments.append(voice_segment)

        for voice_segment in voice_segments:
            await gladia_processor.transcribe(voice_segment, db)

        return audio
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in upload_audio: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to process audio file: {str(e)}"
        )
