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

    def process_audio(self, audio_bytes: bytes) -> Tuple[bytes, float]:
        """Process audio data using Silero VAD"""
        logger.debug(f"Processing audio data of size: {len(audio_bytes)} bytes")
        # Convert bytes to tensor
        audio_tensor, sample_rate = self._load_audio(audio_bytes)
        # Normalize audio signal
        audio_tensor = audio_tensor / torch.max(torch.abs(audio_tensor))
        logger.debug(f"Loaded audio tensor with shape: {audio_tensor.shape}, sample rate: {sample_rate}")
        
        # Get speech timestamps using the utility function
        speech_timestamps = self.get_speech_timestamps(
            audio_tensor,
            self.model,
            sampling_rate=sample_rate,
            threshold=0.1,              # 음성 감지 임계값을 더 낮춤
            min_speech_duration_ms=50,  # 더 짧은 음성도 감지
            min_silence_duration_ms=50, # 더 짧은 무음도 허용
            window_size_samples=512,    # 작은 윈도우 사이즈로 더 세밀한 감지
            speech_pad_ms=30            # 음성 구간 전후로 패딩 추가
        )

        logger.debug(f"Found {len(speech_timestamps)} speech segments")
        if speech_timestamps:
            logger.debug(f"First segment: {speech_timestamps[0]}")
            logger.debug(f"Last segment: {speech_timestamps[-1]}")
            # 각 세그먼트의 길이 정보 출력
            for i, ts in enumerate(speech_timestamps):
                duration = (ts['end'] - ts['start']) / sample_rate
                logger.debug(f"Segment {i}: {duration:.2f}s")

        # Extract speech segments
        speech_segments = []
        for ts in speech_timestamps:
            start_sample = ts['start']
            end_sample = ts['end']
            logger.debug(f"Processing segment: {start_sample} to {end_sample} ({(end_sample-start_sample)/sample_rate:.2f}s)")
            segment = audio_tensor[:, start_sample:end_sample]
            speech_segments.append(segment)

        if not speech_segments:
            logger.warning("No speech segments detected, returning original audio")
            return audio_bytes, 0.0

        # Concatenate speech segments
        processed_audio = torch.cat(speech_segments, dim=1)
        
        # Add small padding to avoid clipping
        if len(processed_audio[0]) > 0:
            pad_size = int(sample_rate * 0.1)  # 0.1초의 패딩
            processed_audio = torch.nn.functional.pad(processed_audio, (pad_size, pad_size))
        
        # Convert back to bytes
        buffer = io.BytesIO()
        torchaudio.save(buffer, processed_audio, sample_rate, format="wav")
        processed_bytes = buffer.getvalue()

        # Calculate speech ratio
        total_duration = len(audio_tensor[0]) / sample_rate
        speech_duration = len(processed_audio[0]) / sample_rate
        speech_ratio = speech_duration / total_duration
        logger.info(f"Total duration: {total_duration:.2f}s, Speech duration: {speech_duration:.2f}s, Ratio: {speech_ratio:.2%}")

        return processed_bytes, speech_ratio, total_duration, speech_duration

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