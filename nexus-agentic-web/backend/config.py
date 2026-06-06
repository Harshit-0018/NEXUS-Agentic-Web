"""
NEXUS Configuration
===================
Loads all settings from environment variables / .env file.
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Azure OpenAI
    AZURE_OPENAI_KEY: str = ""
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4o"
    AZURE_OPENAI_VERSION: str = "2024-08-01-preview"

    # Standard OpenAI (fallback)
    OPENAI_API_KEY: str = ""

    # Pinecone
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX: str = "nexus-memory"

    # Bing Search (optional)
    BING_SEARCH_KEY: str = ""

    # App
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5500", "http://127.0.0.1:5500"]
    MAX_AGENT_STEPS: int = 30
    AGENT_TIMEOUT_SECONDS: int = 120
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
