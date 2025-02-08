from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.audio import Audio as AudioModel
import tempfile
from typing import Dict, Any, List, Tuple
import logging
import torch
import torchaudio
import numpy as np
import io
import soundfile as sf
import warnings
from openai import OpenAI
from core.config import settings

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

    def process_audio(self, audio_bytes: bytes) -> Tuple[List[Dict[str, Any]], float, float, float]:
        """Process audio data using Silero VAD"""
        logger.debug(f"Processing audio data of size: {len(audio_bytes)} bytes")
        # Convert bytes to tensor
        audio_tensor, sample_rate = self._load_audio(audio_bytes)
        # Normalize audio signal
        audio_tensor = audio_tensor / torch.max(torch.abs(audio_tensor))
        total_duration = len(audio_tensor[0]) / sample_rate
        logger.debug(f"Loaded audio tensor with shape: {audio_tensor.shape}, sample rate: {sample_rate}")
        
        # Get speech timestamps using the utility function
        speech_timestamps = self.get_speech_timestamps(
            audio_tensor,
            self.model,
            sampling_rate=sample_rate,
            threshold=0.1,                  # 음성 감지 임계값을 더 낮춤
            min_speech_duration_ms=100,     # 더 짧은 음성도 감지
            min_silence_duration_ms=2000,   # 더 짧은 무음도 허용
            window_size_samples=512,        # 작은 윈도우 사이즈로 더 세밀한 감지
            speech_pad_ms=200               # 음성 구간 전후로 패딩 추가
        )
        logger.debug(f"Found {len(speech_timestamps)} speech segments")

        # Extract speech segments
        speech_segments = []
        speech_duration = 0
        for i, ts in enumerate(speech_timestamps):
            start_sample = ts['start']
            end_sample = ts['end']
            logger.debug(f"Processing segment: {start_sample} to {end_sample} ({(end_sample-start_sample)/sample_rate:.2f}s)")

            audio = audio_tensor[:, start_sample:end_sample]
            duration = (end_sample - start_sample) / sample_rate
            pad_size = int(sample_rate * 1)  # 3초의 패딩
            audio = torch.nn.functional.pad(audio, (pad_size, pad_size))
            buffer = io.BytesIO()
            torchaudio.save(buffer, audio, sample_rate, format="wav")
            speech_segments.append({
                "segment_id": i,
                "buffer": buffer.getvalue(),
                "start_ts": int(ts['start'] / sample_rate * 1000),
                "end_ts": int(ts['end'] / sample_rate * 1000),
            })
            speech_duration += duration
            
        if not speech_segments:
            logger.warning("No speech segments detected, returning original audio")
            return audio_tensor, [], 0.0, total_duration, 0.0
        
        speech_ratio = speech_duration / total_duration
        logger.info(f"Total duration: {total_duration:.2f}s, Speech duration: {speech_duration:.2f}s, Ratio: {speech_ratio:.2%}")
        
        waveform = io.BytesIO()
        torchaudio.save(waveform, audio_tensor, sample_rate, format="wav")

        return waveform.getvalue(), speech_segments, speech_ratio, total_duration, speech_duration

    def _load_audio(self, audio_bytes: bytes) -> Tuple[torch.Tensor, int]:
        """Load audio from bytes into tensor"""
        try:
            # Save bytes to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as temp_file:
                temp_file.write(audio_bytes)
                temp_file.flush()
                
                # Load audio using soundfile
                data, sample_rate = sf.read(temp_file.name)
                # Convert to torch tensor
                waveform = torch.FloatTensor(data)
                if len(waveform.shape) == 1:
                    # If mono, reshape to [1, samples]
                    waveform = waveform.unsqueeze(0)
                else:
                    # If stereo, just take the left channel
                    waveform = waveform[:, 0].unsqueeze(0)
                    # If stereo, convert to mono and reshape to [1, samples]
                    # waveform = waveform.mean(dim=1).unsqueeze(0)
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