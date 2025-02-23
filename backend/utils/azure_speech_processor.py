from fastapi import HTTPException
import tempfile
from core.config import settings
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Tuple
import logging
import azure.cognitiveservices.speech as speechsdk


logger = logging.getLogger(__name__)

class AzureSpeechProcessor:
    def __init__(self):
        if not settings.AZURE_SPEECH_KEY or not settings.AZURE_SPEECH_REGION:
            logger.error("Azure Speech configuration is missing. Skipping AzureSpeechProcessor initialization.")
            return
        self.speech_config = speechsdk.SpeechConfig(
            subscription=settings.AZURE_SPEECH_KEY,
            region=settings.AZURE_SPEECH_REGION
        )

    async def process_transcription(self, speaker_clips: Dict[str, Any]) -> List[Tuple[str, Any]]:
        """Process Azure Speech transcription for all speaker clips"""
        def process_speaker_clip(clip):
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as temp_speaker:
                temp_speaker.write(clip.waveform)
                temp_speaker.flush()
                
                audio_config = speechsdk.AudioConfig(filename=temp_speaker.name)

                speech_recognizer = speechsdk.SpeechRecognizer(
                    speech_config=self.speech_config,
                    audio_config=audio_config
                )
                
                # Start recognition
                logger.info(f"Starting transcription for audio: {clip.speaker}")
                result = speech_recognizer.recognize_once_async().get()
                
                if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    return clip.speaker, result.text
                else:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to transcribe audio: {result.reason}"
                    )
        
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