from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.core.events import create_start_app_handler, create_stop_app_handler
import logging
import requests
import time
from typing import Dict, Optional

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

def get_ngrok_urls(retries=5, delay=2) -> Dict[str, Optional[str]]:
    urls = {
        "backend": None,
        "frontend": None
    }
    
    if settings.NGROK_AUTHTOKEN is None:
        print("NGROK_AUTHTOKEN is not set. Skipping Ngrok URL fetch.")
        return urls

    for _ in range(retries):
        try:
            response = requests.get("http://ngrok:4040/api/tunnels")
            tunnels = response.json().get("tunnels", [])
            
            # Get the URL from the single tunnel
            for tunnel in tunnels:
                if tunnel.get("proto") == "https":
                    base_url = tunnel.get("public_url")
                    if base_url:
                        # Use the same base URL for both services, just add the path
                        urls["backend"] = f"{base_url}/api"
                        urls["frontend"] = base_url
                        break

            if urls["backend"] and urls["frontend"]:
                break

        except requests.RequestException as e:
            print(f"Error fetching Ngrok URL: {e}")
        time.sleep(delay)

    return urls

@app.on_event("startup")
async def startup_event():
    """Event handler that runs when the server starts"""
    ngrok_urls = get_ngrok_urls()
    
    if ngrok_urls["backend"] or ngrok_urls["frontend"]:
        description_lines = [settings.DESCRIPTION, "\nNgrok URLs:\n"]
        
        if ngrok_urls["backend"]:
            print(f"Backend URL: {ngrok_urls['backend']}")
            print(f"Swagger UI: {ngrok_urls['backend']}/docs")
            print(f"ReDoc: {ngrok_urls['backend']}/redoc")
            description_lines.append(f"Backend: {ngrok_urls['backend']}")
            
        if ngrok_urls["frontend"]:
            print(f"Frontend URL: {ngrok_urls['frontend']}")
            description_lines.append(f"Frontend: {ngrok_urls['frontend']}")
            
        app.description = "\n".join(description_lines)
    else:
        print(f"base url: {settings.API_BASE_URL}")
        print(f"Swagger UI: {settings.API_BASE_URL}/docs")
        print(f"ReDoc: {settings.API_BASE_URL}/redoc")
        print("Failed to fetch Ngrok URLs after retries or NGROK_AUTHTOKEN is not set.")

@app.on_event("shutdown")
async def shutdown_event():
    """Event handler that runs when the server shuts down"""
    logger.info("Server shutting down") 