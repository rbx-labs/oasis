from fastapi import APIRouter
from internal.api.v1.routes import transcription

api_router = APIRouter()

api_router.include_router(transcription.router, prefix="/transcription", tags=["transcription"])