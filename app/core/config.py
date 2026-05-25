"""
Steps AI Configuration Management.

This module encapsulates all global settings and API keys using Pydantic Settings V2,
automatically parsing from environmental variable mappings or local .env configuration files.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """
    Application configurations parsed from environmental variables or .env file.
    Utilizes Pydantic Settings V2 for validation and type enforcement.
    """
    PROJECT_NAME: str = "Steps AI Mock Interview Platform"
    ENV: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "info"
    
    # Auth Security settings
    API_KEY: str = "stepsai_hackathon_2026_key"
    REQUIRE_AUTH: bool = False
    
    # Database Settings
    DATABASE_URL: str = "stepsai.db"
    
    # CORS Settings
    CORS_ORIGINS: str = "http://localhost:3000"
    
    # Groq API Settings
    # Sign up at https://console.groq.com (Free Tier)
    GROQ_API_KEY: str = Field(default="", validation_alias="GROQ_API_KEY")

    # Pydantic Configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instantiate settings singleton to be imported across components
settings = Settings()
