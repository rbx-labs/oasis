from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any
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
from app.utils.audio_processing import AudioPreprocessor
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

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize audio preprocessor
audio_preprocessor = AudioPreprocessor()

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
    logger.info(f"Uploading file: {file.filename}, size: {len(await file.read())} bytes")
    await file.seek(0)  # Reset file pointer after reading
    contents = await file.read()
    
    # Process audio with Silero VAD
    try:
        processed_audio, speech_ratio = audio_preprocessor.process_audio(contents)
        logger.info(f"Processed audio file. Speech ratio: {speech_ratio:.2%}")
        
        if speech_ratio < 0.01:  # Less than 1% speech
            raise HTTPException(
                status_code=400,
                detail="No significant speech detected in the audio file"
            )
    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Failed to process audio file"
        )
    
    audio_in = AudioCreate(
        filename=file.filename,
        waveform=processed_audio
    )
    
    existing_audio = crud_audio.get_by_filename(db, filename=file.filename)
    if existing_audio:
        raise HTTPException(
            status_code=400,
            detail="An audio file with this name already exists"
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
    audio = db.query(AudioModel).order_by(AudioModel.created_at.desc()).first()
    if not audio:
        raise HTTPException(
            status_code=404,
            detail="No audio files found"
        )
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
    # Get latest audio
    audio = db.query(AudioModel).order_by(AudioModel.created_at.desc()).first()
    if not audio:
        raise HTTPException(
            status_code=404,
            detail="No audio files found"
        )
    
    try:
        # Create temporary file that will be used across all steps
        temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        try:
            temp_audio.write(audio.waveform)
            temp_audio.flush()
            
            # Step 1: Gladia Diarization
            logger.info("Starting Step 1: Gladia Diarization")
            segments = []
            gladia_response = None
            
            # Call Gladia API for upload
            files = [("audio", (temp_audio.name, open(temp_audio.name, 'rb'), "audio/wav"))]
            headers = {
                'x-gladia-key': settings.GLADIA_API_KEY,
                'accept': 'application/json'
            }
            
            logger.info("Uploading file to Gladia...")
            upload_response = requests.post(
                "https://api.gladia.io/v2/upload/",
                headers=headers,
                files=files
            )
            
            if upload_response.status_code != 200:
                raise HTTPException(
                    status_code=upload_response.status_code,
                    detail=f"Step 1 failed: Gladia API upload error: {upload_response.text}"
                )
            
            upload_result = upload_response.json()
            audio_url = upload_result.get("audio_url")
            
            if not audio_url:
                raise HTTPException(
                    status_code=500,
                    detail="Step 1 failed: Failed to get audio URL from Gladia upload response"
                )
            
            # Request transcription with diarization
            headers['Content-Type'] = 'application/json'
            transcription_data = {
                "audio_url": audio_url,
                "diarization": True
            }
            
            logger.info("Requesting transcription from Gladia API...")
            transcription_response = requests.post(
                "https://api.gladia.io/v2/transcription/",
                headers=headers,
                json=transcription_data
            )
            
            if transcription_response.status_code not in [200, 201]:
                raise HTTPException(
                    status_code=transcription_response.status_code,
                    detail=f"Step 1 failed: Gladia API transcription error: {transcription_response.text}"
                )
            
            transcription_result = transcription_response.json()
            result_url = transcription_result.get("result_url")
            
            if not result_url:
                raise HTTPException(
                    status_code=500,
                    detail="Step 1 failed: Failed to get result URL from Gladia transcription response"
                )
            
            # Poll for results
            while True:
                logger.info("Polling for Gladia results...")
                poll_response = requests.get(result_url, headers=headers)
                
                if poll_response.status_code != 200:
                    raise HTTPException(
                        status_code=poll_response.status_code,
                        detail=f"Step 1 failed: Gladia API polling error: {poll_response.text}"
                    )
                
                poll_result = poll_response.json()
                status = poll_result.get("status")
                
                if status == "done":
                    logger.info("Gladia transcription completed")
                    
                    # Save Gladia API response
                    gladia_response_data = GladiaResponseCreate(
                        audio_id=audio.id,
                        response_data=poll_result
                    )
                    gladia_response = crud_gladia.create(db, obj_in=gladia_response_data)
                    logger.info(f"Saved Gladia API response with ID: {gladia_response.id}")
                    
                    transcription_data = poll_result.get("result", {}).get("transcription", {})
                    utterances = transcription_data.get("utterances", [])
                    
                    if not utterances:
                        raise HTTPException(
                            status_code=500,
                            detail="Step 1 failed: No utterances found in transcription result"
                        )
                    
                    logger.info(f"Processing {len(utterances)} utterances")
                    
                    # Process diarization results
                    for utterance in utterances:
                        if utterance.get('end', 0) - utterance.get('start', 0) >= 1.0:
                            segment_data = DiarizationSegmentCreate(
                                audio_id=audio.id,
                                speaker=f"Speaker_{utterance.get('speaker', 'unknown')}",
                                start_time=utterance.get('start', 0),
                                end_time=utterance.get('end', 0),
                                confidence=utterance.get('confidence', 0),
                                raw_response=utterance
                            )
                            db_segment = crud_diarization.create(db, obj_in=segment_data)
                            segments.append(db_segment)
                    
                    if not segments:
                        raise HTTPException(
                            status_code=500,
                            detail="Step 1 failed: No valid segments created from utterances"
                        )
                    break  # Exit the polling loop when done
                    
                elif status == "error":
                    raise HTTPException(
                        status_code=500,
                        detail=f"Step 1 failed: Gladia transcription failed: {poll_result}"
                    )
                
                # Wait before next poll
                time.sleep(20)
        
            logger.info("Step 1 completed successfully")
            
            # Step 2: Create speaker clips
            logger.info("Starting Step 2: Create speaker clips")
            speaker_clips = {}
            
            try:
                audio_data = AudioSegment.from_wav(temp_audio.name)
                
                for speaker in set(segment.speaker for segment in segments):
                    speaker_segments = [s for s in segments if s.speaker == speaker]
                    combined_audio = AudioSegment.empty()
                    
                    for segment in speaker_segments:
                        start_ms = int(segment.start_time * 1000)
                        end_ms = int(segment.end_time * 1000)
                        segment_audio = audio_data[start_ms:end_ms]
                        combined_audio += segment_audio
                    
                    # Export combined audio for the speaker
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as temp_speaker:
                        combined_audio.export(temp_speaker.name, format='wav')
                        with open(temp_speaker.name, 'rb') as f:
                            speaker_waveform = f.read()
                        
                        speaker_clip_data = SpeakerClipCreate(
                            audio_id=audio.id,
                            speaker=speaker,
                            waveform=speaker_waveform,
                            profile_id=None
                        )
                        db_clip = crud_speaker_clips.create(db, obj_in=speaker_clip_data)
                        speaker_clips[speaker] = db_clip
                
                if not speaker_clips:
                    raise HTTPException(
                        status_code=500,
                        detail="Step 2 failed: No speaker clips created"
                    )
                
                logger.info("Step 2 completed successfully")
                
                # Step 3: Azure Speaker Recognition
                logger.info("Starting Step 3: Azure Speaker Recognition")
                azure_results = {}

                # Collect all existing speaker profile IDs
                existing_profiles = crud_speaker.get_all_profiles(db)
                profile_ids = [profile.profile_id for profile in existing_profiles]

                for speaker, clip in speaker_clips.items():
                    try:
                        with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as temp_speaker:
                            temp_speaker.write(clip.waveform)
                            temp_speaker.flush()
                              # # Convert audio to WAV format with PCM codec
                            # audio_segment = AudioSegment.from_file(io.BytesIO(clip.waveform), format="wav")
                            # audio_segment = audio_segment.set_frame_rate(16000).set_channels(1).set_sample_width(2)
                            # audio_segment.export(temp_speaker.name, format="wav", codec="pcm_s16le")

                            # Identify speaker using Azure's Identify Single Speaker API
                            logger.info(f"Identifying speaker for {speaker}")
                            identify_url = f"https://{settings.AZURE_SPEECH_REGION}.api.cognitive.microsoft.com/speaker-recognition/identification/text-independent/profiles:identifySingleSpeaker?api-version=2021-09-05"
                            headers = {
                                'Ocp-Apim-Subscription-Key': settings.AZURE_SPEECH_KEY,
                                'Content-Type': 'audio/wav'
                            }

                            if profile_ids:
                                params = {
                                    'profileIds': ','.join(profile_ids)
                                }

                                with open(temp_speaker.name, 'rb') as audio_file:
                                    response = requests.post(identify_url, headers=headers, params=params, data=audio_file)

                                if response.status_code == 200:
                                    result = response.json()
                                    identified_profile = result.get("identifiedProfile", {})
                                    profile_id = identified_profile.get("profileId")
                                    score = identified_profile.get("score", 0)

                                    if score >= settings.SPEAKER_IDENTIFICATION_THRESHOLD:
                                        # Use identified profile
                                        logger.info(f"Speaker {speaker} identified as {profile_id} with score {score}")
                                    else:
                                        # No match found, create new profile
                                        profile_id = create_new_profile(headers, temp_speaker)
                                else:
                                    raise HTTPException(
                                        status_code=response.status_code,
                                        detail=f"Failed to identify speaker {speaker}: {response.text}"
                                    )
                            else:
                                # No existing profiles, create new profile
                                profile_id = create_new_profile(headers, temp_speaker)

                            # Get or create speaker profile in the database
                            db_speaker = crud_speaker.get_or_create(
                                db,
                                profile_id=profile_id
                            )
                            logger.info(f"Speaker profile created/retrieved with ID: {db_speaker.id}")

                            # Update speaker clip with the speaker profile reference
                            crud_speaker_clips.update(
                                db,
                                db_obj=clip,
                                obj_in={"profile_id": profile_id}
                            )
                            azure_results[speaker] = profile_id
                            logger.info(f"Updated speaker {speaker} with Azure ID: {profile_id}")

                    except Exception as e:
                        logger.error(f"Error processing speaker {speaker}: {str(e)}")
                        raise HTTPException(
                            status_code=500,
                            detail=f"Step 3 failed: Error processing speaker {speaker}: {str(e)}"
                        )

                if not azure_results:
                    raise HTTPException(
                        status_code=500,
                        detail="Step 3 failed: No speakers were successfully processed"
                    )

                logger.info("Step 3 completed successfully")
                
                # Step 4: Whisper Transcription
                logger.info("Starting Step 4: Whisper Transcription")
                transcription_results = []
                
                def process_speaker_clip(clip):
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as temp_speaker:
                        temp_speaker.write(clip.waveform)
                        temp_speaker.flush()
                        
                        with open(temp_speaker.name, "rb") as audio_file:
                            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                            response = client.audio.transcriptions.create(
                                model="whisper-1",
                                file=audio_file,
                                response_format="verbose_json"
                            )
                            return clip.speaker, response
                
                try:
                    with ThreadPoolExecutor() as executor:
                        transcription_results = list(executor.map(
                            process_speaker_clip,
                            speaker_clips.values()
                        ))
                    
                    if not transcription_results:
                        raise HTTPException(
                            status_code=500,
                            detail="Step 4 failed: No transcription results generated"
                        )
                    
                    logger.info("Step 4 completed successfully")
                    
                    # Step 5: Map Gladia and Whisper results
                    logger.info("Starting Step 5: Mapping results")
                    conversation_data = []
                    logger.info(f"Transcription results: {transcription_results}")
                    for speaker, result in transcription_results:
                        # Get the speaker clip for this speaker to access profile_id
                        speaker_clip = speaker_clips[speaker]
                        profile_id = speaker_clip.profile_id or f"unknown_{speaker.split('_')[-1]}"
                        
                        # Log the result structure to understand what we're working with
                        logger.info(f"Processing Whisper result for {speaker} (Azure ID: {profile_id}): {result}")
                        
                        # New OpenAI API returns segments directly
                        segments = result.segments
                        for segment in segments:
                            conversation_data.append({
                                'speaker': profile_id,
                                'start': segment.start,
                                'end': segment.end,
                                'text': segment.text
                            })
                    
                    if not conversation_data:
                        raise HTTPException(
                            status_code=500,
                            detail="Step 5 failed: No conversation data generated"
                        )
                    
                    # Sort by start time
                    conversation_data.sort(key=lambda x: x['start'])
                    
                    # Step 6: Save conversation data
                    logger.info("Starting Step 6: Saving conversation data")
                    conversation_obj = ConversationCreate(
                        audio_id=audio.id,
                        conversation_data={
                            'segments': conversation_data,
                            'metadata': {
                                'processed_at': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
                                'total_speakers': len(speaker_clips),
                                'total_segments': len(conversation_data)
                            }
                        }
                    )
                    db_conversation = crud_conversation.create(db, obj_in=conversation_obj)
                    
                    logger.info("Step 6 completed successfully")
                    
                    # Process conversation data with OpenAI
                    try:
                        processor = OpenAIProcessor()
                        result = processor.analyze_text(str(db_conversation.conversation_data))
                        return {
                            "request_content": result["request_content"],
                            "message_content": result["message_content"]
                        }
                    except Exception as e:
                        logger.error(f"Error processing conversation with OpenAI: {str(e)}")
                        raise HTTPException(
                            status_code=500,
                            detail=f"OpenAI processing failed: {str(e)}"
                        )
                
                except Exception as e:
                    logger.error(f"Error in Whisper transcription or later steps: {str(e)}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Steps 4-6 failed: {str(e)}"
                    )
                
            except Exception as e:
                logger.error(f"Error in speaker clips creation: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Step 2 failed: {str(e)}"
                )
            finally:
                # Clean up the temporary file
                try:
                    os.unlink(temp_audio.name)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {temp_audio.name}: {str(e)}")
                
        except Exception as e:
            # Clean up the temporary file in case of any error
            try:
                os.unlink(temp_audio.name)
            except Exception as cleanup_error:
                logger.warning(f"Failed to delete temporary file {temp_audio.name}: {str(cleanup_error)}")
            raise e
            
    except Exception as e:
        logger.error(f"Error during audio processing: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

def create_new_profile(headers, temp_speaker):
    logger.info("Creating new profile")
    create_profile_url = f"https://{settings.AZURE_SPEECH_REGION}.api.speaker.azure.com/speaker-recognition/identification/text-independent/profiles?api-version=2021-09-05"
    create_response = requests.post(create_profile_url, headers=headers)
    if create_response.status_code == 201:
        new_profile = create_response.json()
        profile_id = new_profile.get("profileId")
        logger.info(f"Created new profile with ID: {profile_id}")

        # Enroll the speaker
        enroll_url = f"https://{settings.AZURE_SPEECH_REGION}.api.speaker.azure.com/speaker-recognition/identification/text-independent/profiles/{profile_id}/enroll?api-version=2021-09-05"
        with open(temp_speaker.name, 'rb') as audio_file:
            enroll_response = requests.post(enroll_url, headers=headers, data=audio_file)
        if enroll_response.status_code == 200:
            logger.info("Speaker enrolled successfully")
        return profile_id
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to create profile"
        )

