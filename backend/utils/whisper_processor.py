from fastapi import HTTPException
import tempfile
import openai
from core.config import settings
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Tuple
import logging

logger = logging.getLogger(__name__)

class WhisperProcessor:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    async def process_transcription(self, speaker_clips: Dict[str, Any]) -> List[Tuple[str, Any]]:
        """Process Whisper transcription for all speaker clips"""
        def process_speaker_clip(clip):
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as temp_speaker:
                temp_speaker.write(clip.waveform)
                temp_speaker.flush()
                
                with open(temp_speaker.name, "rb") as audio_file:
                    response = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="verbose_json"
                    )
                    return clip.speaker, response
        
        with ThreadPoolExecutor() as executor:
            transcription_results = list(executor.map(
                process_speaker_clip,
                speaker_clips.values()
            ))
        
        if not transcription_results:
            raise HTTPException(
                status_code=500,
                detail="No transcription results generated"
            )
        
        return transcription_results 