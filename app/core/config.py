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
    
    # LLM Keys
    # Note: Anthropic key is the default choice for the Claude interviewer engine
    ANTHROPIC_API_KEY: str = Field(default="", validation_alias="ANTHROPIC_API_KEY")
    GEMINI_API_KEY: str = Field(default="", validation_alias="GEMINI_API_KEY")

    # Pydantic Configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instantiate settings singleton to be imported across components
settings = Settings()
