from fastapi import APIRouter
from app.api.v1.routes import audio, transcription, vision, motion

api_router = APIRouter()

api_router.include_router(audio.router, prefix="/audio", tags=["audio"])
api_router.include_router(transcription.router, prefix="/transcription", tags=["transcription"])
api_router.include_router(vision.router, prefix="/vision", tags=["vision"])
api_router.include_router(motion.router, prefix="/motion", tags=["motion"])