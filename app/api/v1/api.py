from fastapi import APIRouter
from app.api.v1.routes import audio, transcription, cron, vision

api_router = APIRouter()

api_router.include_router(audio.router, prefix="/audio", tags=["audio"])
api_router.include_router(transcription.router, prefix="/transcription", tags=["transcription"])
api_router.include_router(cron.router, prefix="/cron", tags=["cron"]) 
api_router.include_router(vision.router, prefix="/vision", tags=["vision"])