from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl
import os
from pathlib import Path

# Get the root directory (2 levels up from this file)
ROOT_DIR = Path(__file__).parent.parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Backend"
    API_V1_STR: str = "/api/v1"
    
    # BACKEND_CORS_ORIGINS is a comma-separated list of origins
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",  # React frontend
        "http://localhost:8000",  # FastAPI backend
    ]

    # API Keys
    GROQ_API_KEY: Optional[str] = None
    GITHUB_TOKEN: Optional[str] = None

    # Ports
    BACKEND_PORT: str = "8000"
    GITHUB_MCP_PORT: str = "8001"
    FRONTEND_PORT: str = "3000"

    class Config:
        case_sensitive = True
        env_file = str(ROOT_DIR / ".env")

settings = Settings() 