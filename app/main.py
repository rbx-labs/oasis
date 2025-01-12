from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.core.events import create_start_app_handler, create_stop_app_handler
from app.api.v1.routes.cron import initialize_default_schedules
import logging
import requests
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register event handlers
app.add_event_handler("startup", create_start_app_handler())
app.add_event_handler("shutdown", create_stop_app_handler())

# Register API router
app.include_router(api_router, prefix=settings.API_V1_STR)

def get_ngrok_url(retries=5, delay=2):
    if settings.NGROK_AUTHTOKEN is None:
        print("NGROK_AUTHTOKEN is not set. Skipping Ngrok URL fetch.")
        return None

    for _ in range(retries):
        try:
            response = requests.get("http://ngrok:4040/api/tunnels")
            tunnels = response.json().get("tunnels", [])
            for tunnel in tunnels:
                if tunnel.get("proto") == "https":
                    return tunnel.get("public_url")
        except requests.RequestException as e:
            print(f"Error fetching Ngrok URL: {e}")
        time.sleep(delay)
    return None

@app.on_event("startup")
async def startup_event():
    """Event handler that runs when the server starts"""
    logger.info("Initializing default schedules...")
    if initialize_default_schedules():
        logger.info("Default schedules initialized successfully")
    else:
        logger.error("Failed to initialize default schedules")

    ngrok_url = get_ngrok_url()
    if ngrok_url:
        print(f"Ngrok URL: {ngrok_url}")
        print(f"Swagger UI:: {ngrok_url}/docs")
        print(f"ReDoc: {ngrok_url}/redoc")
        app.description = f"{settings.DESCRIPTION}\n\nNgrok URL:\n\n{ngrok_url}"
    else:
        print(f"base url: {settings.API_BASE_URL}")
        print(f"Swagger UI:: {settings.API_BASE_URL}/docs")
        print(f"ReDoc: {settings.API_BASE_URL}/redoc")

        print("Failed to fetch Ngrok URL after retries or NGROK_AUTHTOKEN is not set.")

@app.on_event("shutdown")
async def shutdown_event():
    """Event handler that runs when the server shuts down"""
    from app.api.v1.routes.cron import scheduler
    scheduler.shutdown()
    logger.info("Scheduler shutdown completed") 