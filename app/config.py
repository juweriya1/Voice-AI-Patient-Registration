import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "CareCloud Patient Registration Voice AI"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    BASE_URL: str = "http://localhost:8000"
    
    # Persistent database
    DATABASE_URL: str = "sqlite+aiosqlite:///./carecloud_patients.db"
    
    # Vapi Telephony / Voice AI
    VAPI_API_KEY: Optional[str] = None
    VAPI_PHONE_NUMBER_ID: Optional[str] = None
    VAPI_ASSISTANT_ID: Optional[str] = None
    VAPI_WEBHOOK_SECRET: Optional[str] = None
    PHONE_NUMBER: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
