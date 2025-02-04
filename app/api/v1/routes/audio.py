from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Tuple
from app.api import deps
from app.schemas.audio import (
    Audio, AudioCreate, DiarizationSegment, DiarizationSegmentCreate,
    SpeakerClip, SpeakerClipCreate, Conversation, ConversationCreate,
    GladiaResponseCreate
)
from app.crud.crud_audio import crud_audio
from app.crud.crud_transcription import crud_transcription
from app.crud.crud_diarization import crud_diarization
from app.crud.crud_speaker_clips import crud_speaker_clips
from app.crud.crud_speaker import crud_speaker
from app.crud.crud_conversation import crud_conversation
from app.crud.crud_gladia import crud_gladia
from app.core.security import get_api_key
from app.models.audio import Audio as AudioModel
import azure.cognitiveservices.speech as speechsdk
from app.core.config import settings
from app.utils.openai_processing import OpenAIProcessor
import tempfile
import logging
import os
from app.utils.audio_processor import AudioProcessor
import time
import io
import openai
import requests
import json
from pydub import AudioSegment
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import wave
import array
from app.utils.gladia_processor import GladiaProcessor
from app.utils.whisper_processor import WhisperProcessor
from app.utils.conversation_processor import ConversationProcessor

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
conversation_processor = ConversationProcessor()

router = APIRouter()

@router.get("/all", response_model=List[Audio])
async def read_audios(
    _api_key: str = Depends(get_api_key),
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve audios
    """
    audios = crud_audio.get_multi(db, skip=skip, limit=limit)
    return audios 

@router.post("/upload", response_model=Audio)
async def upload_audio(
    *,
    _api_key: str = Depends(get_api_key),
    db: Session = Depends(deps.get_db),
    file: UploadFile = File(...),
):
    """
    Upload audio file and process waveform using Silero VAD
    """
    existing_audio = crud_audio.get_by_filename(db, filename=file.filename)
    if existing_audio:
        raise HTTPException(
            status_code=400,
            detail="An audio file with this name already exists"
        )
    
    logger.info(f"Uploading file: {file.filename}, size: {len(await file.read())} bytes")
    await file.seek(0)  # Reset file pointer after reading
    contents = await file.read()
    
    # Process audio with Silero VAD
    try:
        processed_audio, speech_ratio, total_duration, speech_duration = audio_processor.process_audio(contents)
        logger.info(f"Processed audio file. Speech ratio: {speech_ratio:.2%}")
    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Failed to process audio file"
        )
    
    audio_in = AudioCreate(
        filename=file.filename,
        waveform=processed_audio,
        total_duration=total_duration,
        speech_duration=speech_duration
    )
    
    audio = crud_audio.create(db, obj_in=audio_in)
    return audio

@router.get("/latest", response_model=Audio)
async def get_latest_audio(
    _api_key: str = Depends(get_api_key),
    db: Session = Depends(deps.get_db)
):
    """
    Get the most recent audio file
    """
    audio = await audio_processor.get_latest_audio(db)
    logger.info(f"Processing audio file: {audio.filename}, created at: {audio.created_at}")
    logger.info(f"Audio data size: {len(audio.waveform)} bytes")
    return audio

@router.get("/{audio_id}", response_model=Audio)
async def get_audio(
    audio_id: int,
    _api_key: str = Depends(get_api_key),
    db: Session = Depends(deps.get_db)
):
    """
    Get a specific audio file by ID
    """
    audio = crud_audio.get(db, id=audio_id)
    if not audio:
        raise HTTPException(
            status_code=404,
            detail=f"Audio with ID {audio_id} not found"
        )
    return audio

@router.get("/download/{audio_id}")
async def download_audio(
    audio_id: int,
    _api_key: str = Depends(get_api_key),
    db: Session = Depends(deps.get_db)
):
    """
    Download a specific audio file
    """
    audio = crud_audio.get(db, id=audio_id)
    if not audio:
        raise HTTPException(
            status_code=404,
            detail=f"Audio with ID {audio_id} not found"
        )
    
    logger.info(f"Downloading audio file: {audio.filename}, size: {len(audio.waveform)} bytes")
    
    # Create in-memory stream
    stream = io.BytesIO(audio.waveform)
    
    # Return streaming response
    return StreamingResponse(
        stream,
        media_type="audio/wav",
        headers={
            'Content-Disposition': f'attachment; filename="{audio.filename}"'
        }
    )

@router.get("/download/latest")
async def download_latest_audio(
    _api_key: str = Depends(get_api_key),
    db: Session = Depends(deps.get_db)
):
    """
    Download the most recent audio file
    """
    audio = db.query(AudioModel).order_by(AudioModel.created_at.desc()).first()
    if not audio:
        raise HTTPException(
            status_code=404,
            detail="No audio files found"
        )
    
    logger.info(f"Downloading latest audio file: {audio.filename}, size: {len(audio.waveform)} bytes")
    
    # Create in-memory stream
    stream = io.BytesIO(audio.waveform)
    
    # Return streaming response
    return StreamingResponse(
        stream,
        media_type="audio/wav",
        headers={
            'Content-Disposition': f'attachment; filename="{audio.filename}"'
        }
    )

@router.post("/latest/transcribe")
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

@router.post("/latest/transcribe2")
async def transcribe_latest_audio_whisper(
    _api_key: str = Depends(get_api_key),
    db: Session = Depends(deps.get_db)
):
    """
    Transcribe the latest audio file using OpenAI Whisper
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
            
            # Transcribe using OpenAI Whisper
            logger.info(f"Starting Whisper transcription for audio: {audio.filename}")
            with open(temp_audio.name, "rb") as audio_file:
                result = openai.Audio.transcribe(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            # Create transcription
            transcription_data = TranscriptionCreate(
                text=result,
                audio_id=audio.id
            )
            db_transcription = crud_transcription.create(db, obj_in=transcription_data)
            logger.info(f"Whisper transcription saved with ID: {db_transcription.id}")
            
            return {
                "message": "Whisper transcription completed successfully",
                "transcription": db_transcription
            }
                
    except Exception as e:
        logger.error(f"Error during Whisper transcription: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/gladia/latest")
async def process_latest_audio_with_gladia(
    _api_key: str = Depends(get_api_key),
    db: Session = Depends(deps.get_db)
):
    """
    Process the latest audio file with Gladia API for diarization and transcription
    """
    try:
        # Step 1: Get latest audio
        audio = await audio_processor.get_latest_audio(db)
        
        # Create temporary file for processing
        temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        try:
            temp_audio.write(audio.waveform)
            temp_audio.flush()
            
            # Step 2: Gladia Diarization
            logger.info("Starting Step 1: Gladia Diarization")
            audio_url = await gladia_processor.upload_to_gladia(temp_audio.name)
            segments = await gladia_processor.process_diarization(audio_url, audio.id, db)
            logger.info("Step 1 completed successfully")
            
            # Step 3: Create speaker clips
            logger.info("Starting Step 2: Create speaker clips")
            audio_data = AudioSegment.from_wav(temp_audio.name)
            speaker_clips = await audio_processor.create_speaker_clips(audio_data, segments, audio.id, db)
            logger.info("Step 2 completed successfully")
            
            # Step 4: Gladia Speaker Reidentification
            logger.info("Starting Step 3: Gladia Speaker Reidentification")
            speaker_results = {}
            for speaker, clip in speaker_clips.items():
                try:
                    result = await gladia_processor.process_speaker_reidentification(speaker, clip, db)
                    speaker_results[speaker] = {
                        "profile_id": result["profile_id"],
                        "transcript": result["transcript"]
                    }
                    # Save speaker_results to Conversation
                    conversation_data = {
                        "speaker": result["profile_id"],
                        "content": result["transcript"]
                    }
                    # TODO: Uncomment this when ready
                    # await conversation_processor.create_conversation(
                    #     audio_id=audio.id,
                    #     conversation_data=conversation_data,
                    #     db=db
                    # )
                except Exception as e:
                    logger.error(f"Error processing speaker {speaker}: {str(e)}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Error processing speaker {speaker}: {str(e)}"
                    )
            logger.info("Step 3 completed successfully")
            
            # # Step 5: Whisper Transcription
            # logger.info("Starting Step 5: Whisper Transcription")
            # transcription_results = await whisper_processor.process_transcription(speaker_clips)
            # print("transcription_results", transcription_results)
            # logger.info("Step 5 completed successfully")
            
            # Step 6: Create conversation
            # logger.info("Starting Step 6: Creating conversation")
            # db_conversation = await conversation_processor.create_conversation(audio.id, speaker_clips, speaker_results, db)
            # print("db_conversation", db_conversation)
            # logger.info("Step 6 completed successfully")
            
            # Process conversation with OpenAI
            try:
                processor = OpenAIProcessor()
                
                # Format the conversation data
                conversation_data = []
                for speaker, data in speaker_results.items():
                    conversation_data.append({
                        "speaker": data["profile_id"],
                        "content": data["transcript"]
                    })
                print("conversation_data", conversation_data)
                result = processor.analyze_text(conversation_data)
                return result
            except Exception as e:
                logger.error(f"Error processing conversation with OpenAI: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"OpenAI processing failed: {str(e)}"
                )
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_audio.name)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_audio.name}: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error during audio processing: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

