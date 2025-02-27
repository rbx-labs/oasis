from fastapi import APIRouter
from internal.api.v1.routes import transcription
from internal.api.v1.routes import speaker

api_router = APIRouter()

api_router.include_router(transcription.router, prefix="/transcription", tags=["transcription"])
api_router.include_router(speaker.router, prefix="/speaker", tags=["speaker"])