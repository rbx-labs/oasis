from typing import Callable
from fastapi import FastAPI
from db.session import engine
from db.base import Base

def create_start_app_handler() -> None:
    # Create database tables on startup
    Base.metadata.create_all(bind=engine)

def create_stop_app_handler() -> None:
    pass