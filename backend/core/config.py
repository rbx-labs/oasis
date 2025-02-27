from typing import List, Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Oasis"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Oasis API Server"
    API_V1_STR: str = "/api/v1"
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = ["http://localhost:8081"]
    
    # API Key settings
    API_KEY: str

    # Database settings
    POSTGRES_HOST: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    
    # Azure Speech Settings
    AZURE_SPEECH_KEY: Optional[str] = None
    AZURE_SPEECH_REGION: Optional[str] = None
    
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