from fastapi import FastAPI
from core.config import settings
from internal.api.v1.api import api_router
from contextlib import asynccontextmanager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield  # Server is running

    # Shutdown
    logger.info("Server shutting down")

app = FastAPI(
    lifespan=lifespan
)

# Register API router
logger.info(f"Registering API router with prefix: {settings.API_V1_STR}")
app.include_router(api_router, prefix=settings.API_V1_STR)
