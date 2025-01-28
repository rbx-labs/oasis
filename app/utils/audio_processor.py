from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.audio import Audio as AudioModel
import tempfile
from pydub import AudioSegment
from typing import Dict, Any, List, Tuple
from app.schemas.audio import SpeakerClipCreate
from app.crud.crud_speaker_clips import crud_speaker_clips
import logging
import torch
import torchaudio
import numpy as np
import io
import soundfile as sf
import warnings
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            logger.info("Loading Silero VAD model...")
            self.model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                verbose=False
            )
            self.get_speech_timestamps = utils[0]
        self.model.eval()
        logger.info("Model loaded successfully")

    async def get_latest_audio(self, db: Session) -> AudioModel:
        """Get the latest audio file from database"""
        audio = db.query(AudioModel).order_by(AudioModel.created_at.desc()).first()
        if not audio:
            raise HTTPException(
                status_code=404,
                detail="No audio files found"
            )
        return audio

    async def create_speaker_clips(self, audio_data: AudioSegment, segments: List[Any], audio_id: int, db: Session) -> Dict[str, Any]:
        """Create speaker clips from segments"""
        speaker_clips = {}
        
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
                    audio_id=audio_id,
                    speaker=speaker,
                    waveform=speaker_waveform,
                    profile_id=None
                )
                db_clip = crud_speaker_clips.create(db, obj_in=speaker_clip_data)
                speaker_clips[speaker] = db_clip
        
        if not speaker_clips:
            raise HTTPException(
                status_code=500,
                detail="No speaker clips created"
            )
        
        return speaker_clips

    def process_audio(self, audio_bytes: bytes) -> Tuple[List[Dict[str, Any]], float]:
        """Process audio data using Silero VAD and return individual segments"""
        logger.debug(f"Processing audio data of size: {len(audio_bytes)} bytes")
        audio_tensor, sample_rate = self._load_audio(audio_bytes)
        audio_tensor = audio_tensor / torch.max(torch.abs(audio_tensor))
        logger.debug(f"Loaded audio tensor with shape: {audio_tensor.shape}, sample rate: {sample_rate}")
        
        speech_timestamps = self.get_speech_timestamps(
            audio_tensor,
            self.model,
            sampling_rate=sample_rate,
            threshold=0.1,
            min_speech_duration_ms=50,
            min_silence_duration_ms=50,
            window_size_samples=512,
            speech_pad_ms=30
        )

        logger.debug(f"Found {len(speech_timestamps)} speech segments")
        
        segments = []
        total_speech_duration = 0.0
        
        for ts in speech_timestamps:
            start_sample = ts['start']
            end_sample = ts['end']
            start_time = start_sample / sample_rate
            end_time = end_sample / sample_rate
            duration = end_time - start_time
            
            segment = audio_tensor[:, start_sample:end_sample]
            
            # Convert segment to bytes
            buffer = io.BytesIO()
            torchaudio.save(buffer, segment, sample_rate, format="wav")
            segment_bytes = buffer.getvalue()
            
            segments.append({
                'start_time': start_time,
                'end_time': end_time,
                'waveform': segment_bytes
            })
            
            total_speech_duration += duration
            logger.debug(f"Processed segment: {start_time:.2f}s to {end_time:.2f}s ({duration:.2f}s)")
        
        if not segments:
            logger.warning("No speech segments detected")
            return [], 0.0
        
        total_duration = len(audio_tensor[0]) / sample_rate
        speech_ratio = total_speech_duration / total_duration
        logger.info(f"Total duration: {total_duration:.2f}s, Speech duration: {total_speech_duration:.2f}s, Ratio: {speech_ratio:.2%}")
        
        return segments, speech_ratio

    def _load_audio(self, audio_bytes: bytes) -> Tuple[torch.Tensor, int]:
        """Load audio from bytes into tensor"""
        try:
            # Save bytes to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as temp_file:
                temp_file.write(audio_bytes)
                temp_file.flush()
                
                # Load audio using soundfile
                data, sample_rate = sf.read(temp_file.name)
                # Convert to torch tensor and reshape for model
                waveform = torch.FloatTensor(data)
                if len(waveform.shape) == 1:
                    waveform = waveform.unsqueeze(0)
                else:
                    waveform = waveform.mean(dim=1, keepdim=True)  # Convert stereo to mono
                logger.debug(f"Successfully loaded audio file with sample rate: {sample_rate}")
                return waveform, sample_rate
        except Exception as e:
            logger.error(f"Error loading audio: {str(e)}")
            raise

    def transcribe_with_whisper(self, audio_bytes: bytes) -> str:
        """Transcribe audio using OpenAI's Whisper model"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as temp_file:
                temp_file.write(audio_bytes)
                temp_file.flush()
                
                with open(temp_file.name, "rb") as audio_file:
                    transcript = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="ko",
                        response_format="text"
                    )
                
                logger.info("Successfully transcribed audio using Whisper")
                return transcript
        except Exception as e:
            logger.error(f"Whisper transcription error: {str(e)}")
            raise   