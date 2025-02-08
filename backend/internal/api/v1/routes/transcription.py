import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import session
from core.security import get_api_key
from utils.openai_processor import OpenAIProcessor
import logging
from datetime import datetime
from models.audio import Audio as AudioModel
from models.voice_segment import VoiceSegment
from models.gladia_response import GladiaResponse
from models.speaker import Speaker

# Configure logging
logger = logging.getLogger(__name__)
openai_processor = OpenAIProcessor()

router = APIRouter()

@router.get("/latest/analyze")
async def analyze_latest_transcription(
    _api_key: str = Depends(get_api_key),
    db: Session = Depends(session.get_db)
):
    """
    Analyze the oldest unprocessed transcription using OpenAI by formatting voice segments with timestamps and speakers
    """
    # Get the oldest unprocessed audio
    latest_audio = (
        db.query(AudioModel)
        .filter(AudioModel.processed == False)
        .order_by(AudioModel.created_at.asc())
        .first()
    )
    
    if not latest_audio:
        raise HTTPException(
            status_code=200,
            detail="No unprocessed audio recordings found"
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

    # Collect all unique speaker UUIDs from the transcription
    speaker_uuids = set()
    for segment, gladia_response in voice_segments:
        response_data = gladia_response.response_data
        if (response_data and 
            "result" in response_data and 
            "speaker_reidentification" in response_data["result"] and 
            "results" in response_data["result"]["speaker_reidentification"]):
            speaker_results = response_data["result"]["speaker_reidentification"]["results"]
            speakers = speaker_results if isinstance(speaker_results, list) else list(speaker_results.values())
            for speaker in speakers:
                speaker_uuid = speaker[0].get("uuid")
                if speaker_uuid:
                    speaker_uuids.add(speaker_uuid)

    # Query speakers from the database
    speakers_map = {}
    speaker_contexts = {}
    db_speakers = db.query(Speaker).filter(Speaker.profile_id.in_(speaker_uuids)).all()
    for speaker in db_speakers:
        speakers_map[speaker.profile_id] = speaker.speaker_label if speaker.speaker_label else speaker.profile_id
        speaker_contexts[speaker.profile_id] = speaker.context

    # Format the conversation text with speaker labels
    formatted_text = []
    for segment, gladia_response in voice_segments:
        response_data = gladia_response.response_data
        if response_data and "result" in response_data:
            utterances = response_data["result"]["transcription"]["utterances"]
            speaker_results = response_data["result"]["speaker_reidentification"]["results"]
            
            for utterance in utterances:
                speaker_id = str(utterance.get("speaker"))
                text = utterance.get("text", "")
                start = utterance.get("start", 0)
                timestamp = datetime.fromtimestamp(segment.start_time / 1000 + start).strftime("%-m/%-d %-I:%M:%S%p")
                
                # Get UUID from speaker reidentification results
                speaker_uuid = None
                if speaker_id in speaker_results and speaker_results[speaker_id]:
                    speaker_uuid = speaker_results[speaker_id][0].get("uuid")
                
                if speaker_uuid and speaker_uuid in speakers_map:
                    # Use speaker label from map, fallback to Speaker_X if not found
                    speaker_label = speakers_map.get(speaker_uuid)
                    formatted_text.append(f"{timestamp} [{speaker_label}]: {text}")
    
    formatted_text = "\n".join(formatted_text)
    
    try:
        analysis = openai_processor.analyze_text(formatted_text)
        # Mark the audio as processed
        latest_audio.processed = True
        db.commit()
        logger.info(f"Generated analysis for audio {latest_audio.id} and marked as processed")
    except Exception as e:
        db.rollback()
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to analyze conversation"
        )
    logger.info(speakers_map)
    for speaker_uuid, speaker_label in speakers_map.items():
        try:
            analysis = openai_processor.speaker_analysis(
                speaker_label=speaker_label,
                conversation=formatted_text,
                previous_context=speaker_contexts.get(speaker_uuid, None)
            )
            logger.info(analysis)
            analysis_data = json.loads(analysis["response"])
            speaker = db.query(Speaker).filter(Speaker.profile_id == speaker_uuid).first()
            if speaker:
                speaker.speaker_label = analysis_data.get("speaker_label")
                speaker.context = analysis_data["context"]
                db.commit()
                logger.info(f"Updated speaker {speaker_uuid} with new analysis data")
            else:
                logger.info(f"Speaker {speaker_uuid} not found in database")
        except Exception as e:
            logger.error(f"Failed to analyze speaker {speaker_label}: {str(e)}")
    
    return {
        "audio_id": latest_audio.id,
        "text": formatted_text,
        "analysis": analysis["response"],
    }