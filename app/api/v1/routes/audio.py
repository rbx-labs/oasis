from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.audio import (
    Audio, AudioCreate
)
from app.schemas.voice_segment import VoiceSegmentCreate
from app.crud.crud_audio import crud_audio
from app.crud.crud_voice_segment import crud_voice_segment
from app.crud.crud_transcription import crud_transcription
from app.core.security import get_api_key
from app.models.audio import Audio as AudioModel
import azure.cognitiveservices.speech as speechsdk
from app.core.config import settings
import tempfile
import logging
from app.utils.audio_processor import AudioProcessor
from app.utils.gladia_processor import GladiaProcessor
from app.utils.whisper_processor import WhisperProcessor
from app.schemas.transcription import TranscriptionCreate

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

router = APIRouter()

@router.post("/upload", response_model=Audio)
async def upload_audio(
    *,
    _api_key: str = Depends(get_api_key),
    db: Session = Depends(deps.get_db),
    file: UploadFile = File(...),
    start_timestamp: int = Form(...)
):
    """
    Upload audio file and process waveform using Silero VAD
    
    Parameters:
    - file: Audio file to upload
    - start_timestamp: Unix timestamp for the audio file
    """
    existing_audio = crud_audio.get_by_filename(db, filename=file.filename)
    if existing_audio:
        crud_audio.remove(db, id=existing_audio.id)
        
    await file.seek(0)  # Reset file pointer after reading
    contents = await file.read()
    logger.info(f"Uploading file: {file.filename}, start_timestamp: {start_timestamp}, size: {len(await file.read())} bytes")
    
    # Process audio with Silero VAD
    try:
        segments, speech_ratio, total_duration, speech_duration = audio_processor.process_audio(contents)
        logger.info(f"Processed audio file. Speech ratio: {speech_ratio:.2%}")
    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Failed to process audio file"
        )
    
    audio_in = AudioCreate(
        filename=file.filename,
        waveform=contents,
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

# TODO: Temporarily commented out as we may use Azure Speech
# @router.post("/latest/transcribe")
async def transcribe_latest_audio(
    _api_key: str = Depends(get_api_key),
    db: Session = Depends(deps.get_db)
):
    """
    Transcribe the latest audio file using Azure Speech-to-Text
    """
    # Get latest audio
    audio = db.query(AudioModel).order_by(AudioModel.created_at.desc()).first()
    if not audio:
        raise HTTPException(
            status_code=404,
            detail="No audio files found"
        )
    
    try:
        # Create temporary file for audio data
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as temp_audio:
            temp_audio.write(audio.waveform)
            temp_audio.flush()
            
            # Initialize Azure Speech config
            speech_config = speechsdk.SpeechConfig(
                subscription=settings.AZURE_SPEECH_KEY,
                region=settings.AZURE_SPEECH_REGION
            )
            
            # Create audio config from file
            audio_config = speechsdk.AudioConfig(filename=temp_audio.name)
            
            # Create speech recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config,
                audio_config=audio_config
            )
            
            # Start recognition
            logger.info(f"Starting transcription for audio: {audio.filename}")
            result = speech_recognizer.recognize_once_async().get()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                # Create transcription
                transcription_data = TranscriptionCreate(
                    text=result.text,
                    audio_id=audio.id
                )
                db_transcription = crud_transcription.create(db, obj_in=transcription_data)
                logger.info(f"Transcription saved with ID: {db_transcription.id}")
                
                return {
                    "message": "Transcription completed successfully",
                    "transcription": db_transcription
                }
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to transcribe audio: {result.reason}"
                )
                
    except Exception as e:
        logger.error(f"Error during transcription: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

