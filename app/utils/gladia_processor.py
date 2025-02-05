from fastapi import HTTPException
import requests
import logging
from app.core.config import settings
from app.models.voice_segment import VoiceSegment
from app.schemas.audio import DiarizationSegmentCreate
from app.schemas.gladia_response import GladiaResponseCreate
from app.crud.crud_gladia import crud_gladia
from app.crud.crud_diarization import crud_diarization
from app.crud.crud_speaker import crud_speaker
from sqlalchemy.orm import Session
import time
import tempfile
from typing import List, Any

logger = logging.getLogger(__name__)

class GladiaProcessor:
    def __init__(self):
        self.headers = {
            'x-gladia-key': settings.GLADIA_API_KEY,
            'accept': 'application/json'
        }

    async def upload_to_gladia(self, file_path: str) -> str:
        """Upload audio file to Gladia API and return audio URL"""
        files = [("audio", (file_path, open(file_path, 'rb'), "audio/wav"))]
        
        logger.info("Uploading file to Gladia...")
        upload_response = requests.post(
            "https://api.gladia.io/v2/upload/",
            headers=self.headers,
            files=files
        )
        
        if upload_response.status_code != 200:
            raise HTTPException(
                status_code=upload_response.status_code,
                detail=f"Gladia API upload error: {upload_response.text}"
            )
        
        upload_result = upload_response.json()
        audio_url = upload_result.get("audio_url")
        
        if not audio_url:
            raise HTTPException(
                status_code=500,
                detail="Failed to get audio URL from Gladia upload response"
            )
        
        return audio_url

    async def process_diarization(self, audio_url: str, audio_id: int, db: Session) -> List[Any]:
        """Process audio with Gladia diarization and return segments"""
        headers = {**self.headers, 'Content-Type': 'application/json'}
        
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
                detail=f"Gladia API transcription error: {transcription_response.text}"
            )
        
        transcription_result = transcription_response.json()
        result_url = transcription_result.get("result_url")
        
        if not result_url:
            raise HTTPException(
                status_code=500,
                detail="Failed to get result URL from Gladia transcription response"
            )
        
        segments = []
        
        # Poll for results
        while True:
            logger.info("Polling for Gladia results...")
            poll_response = requests.get(result_url, headers=headers)
            
            if poll_response.status_code != 200:
                raise HTTPException(
                    status_code=poll_response.status_code,
                    detail=f"Gladia API polling error: {poll_response.text}"
                )
            
            poll_result = poll_response.json()
            status = poll_result.get("status")
            
            if status == "done":
                logger.info("Gladia transcription completed")
                
                # Save Gladia API response
                gladia_response_data = GladiaResponseCreate(
                    audio_id=audio_id,
                    response_data=poll_result
                )
                gladia_response = crud_gladia.create(db, obj_in=gladia_response_data)
                logger.info(f"Saved Gladia API response with ID: {gladia_response.id}")
                
                transcription_data = poll_result.get("result", {}).get("transcription", {})
                utterances = transcription_data.get("utterances", [])
                
                if not utterances:
                    raise HTTPException(
                        status_code=500,
                        detail="No utterances found in transcription result"
                    )
                
                logger.info(f"Processing {len(utterances)} utterances")
                
                # Process diarization results
                for utterance in utterances:
                    if utterance.get('end', 0) - utterance.get('start', 0) >= 1.0:
                        segment_data = DiarizationSegmentCreate(
                            audio_id=audio_id,
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
                        detail="No valid segments created from utterances"
                    )
                break
                
            elif status == "error":
                raise HTTPException(
                    status_code=500,
                    detail=f"Gladia transcription failed: {poll_result}"
                )
            
            time.sleep(20)
        
        return segments
    
    async def transcribe(self, voice_segment: VoiceSegment, db: Session) -> dict:
        """Transcribe a voice segment"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as temp_clip:
            temp_clip.write(voice_segment.waveform)
            temp_clip.flush()
            
            audio_url = await self.upload_to_gladia(temp_clip.name)
            headers = {**self.headers, 'Content-Type': 'application/json'}
            response = requests.post(
                "https://api.gladia.io/v2/transcription/",
                headers=headers,
                json={
                    "audio_url": audio_url,
                    "diarization": True,
                    "speaker_reidentification": True,
                    "speaker_reidentification_config": {
                        "filters": {},
                        "save_new_speakers": True,
                        "save_new_speaker_similarity_threshold": 0.95,
                        "boost_uuids": []
                    }
                }
            )

            if response.status_code not in [200, 201]:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Speaker reidentification failed: {response.text}"
                )
            
            result = response.json()
            result_url = result.get("result_url")
            
            if not result_url:
                raise HTTPException(
                    status_code=500,
                    detail="No result URL received from Gladia API"
                )
            
            while True:
                poll_response = requests.get(result_url, headers=headers)
                
                if poll_response.status_code != 200:
                    raise HTTPException(
                        status_code=poll_response.status_code,
                        detail=f"Failed to poll results: {poll_response.text}"
                    )
                
                poll_result = poll_response.json()
                
                status = poll_result.get("status")
                
                if status == "done":
                    # Save Gladia API response
                    gladia_response_data = GladiaResponseCreate(
                        voice_segment_id=voice_segment.id,
                        response_data=poll_result
                    )
                    gladia_response = crud_gladia.create(db, obj_in=gladia_response_data)
                    logger.info(f"Saved Gladia API response with ID: {gladia_response.id}")
                    
                    speaker_info = poll_result.get("result", {}).get("speaker_reidentification", {})
                    
                    if not speaker_info:
                        logger.warning("No speaker reidentification info in response")
                        speaker_info = {}
                    
                    # Get UUID from speaker_reidentification results
                    speaker_results = speaker_info.get("results", {})
                    speakers = speaker_results if isinstance(speaker_results, list) else list(speaker_results.values())
                    for speaker in speakers:
                        profile_id = speaker[0].get("uuid")
                    
                        # Get or create speaker profile in database
                        db_speaker = crud_speaker.get_or_create(
                            db,
                            profile_id=profile_id
                        )
                        logger.info(f"Speaker profile created/retrieved with ID: {db_speaker.profile_id}")
                    break
                elif status == "error":
                    raise HTTPException(
                        status_code=500,
                        detail=f"Speaker reidentification failed: {poll_result}"
                    )
                
                time.sleep(10)

    async def process_speaker_reidentification(self, speaker: str, clip: Any, db: Session) -> dict:
        """Process speaker reidentification for a single speaker"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as temp_speaker:
            temp_speaker.write(clip.waveform)
            temp_speaker.flush()
            
            audio_url = await self.upload_to_gladia(temp_speaker.name)
            
            headers = {**self.headers, 'Content-Type': 'application/json'}
            
            reidentification_data = {
                "audio_url": audio_url,
                "diarization": True,
                "speaker_reidentification": True,
                "speaker_reidentification_config": {
                    "filters": {},
                    "save_new_speakers": True,
                    "save_new_speaker_similarity_threshold": 0.95,
                    "boost_uuids": []
                }
            }
            
            response = requests.post(
                "https://api.gladia.io/v2/transcription/",
                headers=headers,
                json=reidentification_data
            )
            
            if response.status_code not in [200, 201]:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Speaker reidentification failed: {response.text}"
                )
            
            result = response.json()
            result_url = result.get("result_url")
            
            if not result_url:
                raise HTTPException(
                    status_code=500,
                    detail="No result URL received from Gladia API"
                )
            
            while True:
                poll_response = requests.get(result_url, headers=headers)
                
                if poll_response.status_code != 200:
                    raise HTTPException(
                        status_code=poll_response.status_code,
                        detail=f"Failed to poll results: {poll_response.text}"
                    )
                
                poll_result = poll_response.json()
                
                status = poll_result.get("status")
                
                if status == "done":
                    print("poll_result", poll_result)
                    speaker_info = poll_result.get("result", {}).get("speaker_reidentification", {})
                    
                    if not speaker_info:
                        logger.warning("No speaker reidentification info in response")
                        speaker_info = {}
                    
                    # Get UUID from speaker_reidentification results
                    speaker_results = speaker_info.get("results", {}).get("0", [])
                    profile_id = speaker_results[0].get("uuid") if speaker_results else None
                    
                    if not profile_id:
                        profile_id = f"unknown_{speaker.split('_')[-1]}"
                        logger.warning(f"Using fallback profile ID: {profile_id}")
                    
                    # Get or create speaker profile in database
                    db_speaker = crud_speaker.get_or_create(
                        db,
                        profile_id=profile_id
                    )
                    logger.info(f"Speaker profile created/retrieved with ID: {db_speaker.profile_id}")
                    
                    # Update speaker clip with profile reference
                    # crud_speaker_clips.update(
                    #     db,
                    #     db_obj=clip,
                    #     obj_in={"profile_id": profile_id}
                    # )
                    # Get full transcript from the response
                    full_transcript = poll_result.get("result", {}).get("transcription", {}).get("full_transcript", "")
                    
                    return {
                        "profile_id": db_speaker.profile_id,
                        "transcript": full_transcript
                    }
                
                elif status == "error":
                    raise HTTPException(
                        status_code=500,
                        detail=f"Speaker reidentification failed: {poll_result}"
                    )
                
                time.sleep(20) 