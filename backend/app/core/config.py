import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    GROQ_API_KEY: str = "mocked_key"
    GROQ_MODEL: str = "groq/compound"
    FALLBACK_MODEL: str = "llama-3.3-70b-versatile"
    DATABASE_URL: str = "sqlite:///./crm.db"
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    LOG_LEVEL: str = "INFO"
    PORT: int = 8000

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
