from fastapi import APIRouter
from api.v1.routes import audio, vision, motion, llm

api_router = APIRouter()

api_router.include_router(audio.router, prefix="/audio", tags=["audio"])
api_router.include_router(vision.router, prefix="/vision", tags=["vision"])
api_router.include_router(motion.router, prefix="/motion", tags=["motion"])
api_router.include_router(llm.router, prefix="/llm", tags=["llm"])