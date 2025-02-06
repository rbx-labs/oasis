from typing import List, Optional
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Oasis"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Oasis API Server"
    API_V1_STR: str = "/api/v1"
    
    # API Base URL
    API_BASE_URL: str = "http://localhost:8000"

    # CORS settings
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # API Key settings
    API_KEY: str

    # Database settings
    POSTGRES_HOST: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    
    # Azure Speech Settings
    AZURE_SPEECH_KEY: str
    AZURE_SPEECH_REGION: str
    
    # OpenAI API Key
    OPENAI_API_KEY: str
    
    # Gladia API Key
    GLADIA_API_KEY: str
    
    # NGROK_AUTHTOKEN
    NGROK_AUTHTOKEN: Optional[str] = None
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings() 