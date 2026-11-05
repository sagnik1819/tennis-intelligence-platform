"""
Module 5: Core Application Configuration
Loads environment variables, manages CORS domains, and sets API prefixes.
"""
import os
from typing import List

class Settings:
    PROJECT_NAME: str = "Tennis Intelligence Platform API"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # CORS Origins - Allow React frontend (Vite default: 5173, CRA: 3000, production)
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ]
    
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()
