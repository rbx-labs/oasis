from typing import Callable
from fastapi import FastAPI
from app.db.session import engine
from app.db.base import Base

def create_start_app_handler() -> Callable:
    async def start_app() -> None:
        # Create database tables on startup
        Base.metadata.create_all(bind=engine)
    return start_app

def create_stop_app_handler() -> Callable:
    async def stop_app() -> None:
        # Cleanup tasks on shutdown
        pass
    return stop_app 