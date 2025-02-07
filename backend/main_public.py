from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from api.v1.api import api_router
from core.events import create_start_app_handler, create_stop_app_handler
import logging
import requests
import time
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_start_app_handler()
    retries = 5
    delay = 2

    # Startup
    if settings.NGROK_AUTHTOKEN is None:
        print("NGROK_AUTHTOKEN is not set. Skipping Ngrok URL fetch.")
    else:
        for _ in range(retries):
            try:
                response = requests.get("http://ngrok:4040/api/tunnels")
                tunnels = response.json().get("tunnels", [])
                
                # Get the URL from the single tunnel
                for tunnel in tunnels:
                    if tunnel.get("proto") == "https":
                        base_url = tunnel.get("public_url")
                
                if base_url:
                    break
            except requests.RequestException as e:
                print(f"Error fetching Ngrok URL: {e}")
            time.sleep(delay)
        if base_url:
            print(f'Ngrok URL: {base_url}')
        else:
            print("Failed to fetch Ngrok URLs after retries or NGROK_AUTHTOKEN is not set.")
    
    yield  # Server is running
    
    create_stop_app_handler()
    
    # Shutdown
    logger.info("Server shutting down")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API router
logger.info(f"Registering API router with prefix: {settings.API_V1_STR}")
app.include_router(api_router, prefix=settings.API_V1_STR)