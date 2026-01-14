from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Central application configuration.
    Loaded once and shared across the app.
    """

    # App
    APP_NAME: str = "ContentLens_AI"
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # Ollama (LLM Runtime)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL_EXTRACTOR: str = "llama3.1"
    OLLAMA_MODEL_ROUTER: str = "mistral"

    OLLAMA_MODEL_SUMMARIZER: str = "llama3.1"
    OLLAMA_MODEL_TRANSLATOR: str = "mistral"
    OLLAMA_MODEL_ANALYZER: str = "llama3.1"
    OLLAMA_MODEL_RECOMMENDER: str = "llama3.1"

    # Marketing / additional models
    OLLAMA_MODEL_IDEATION: str = "llama3.1"
    OLLAMA_MODEL_COPYWRITER: str = "llama3.1"


    # Langfuse (Observability)
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_SECRET_KEY: Optional[str] = None
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    # File Processing
    MAX_FILE_SIZE_MB: int = 20
    ALLOWED_EXTENSIONS: str = "pdf,docx,txt,png,jpg,jpeg"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings object.
    Ensures settings are loaded once per process.
    """
    return Settings()


# Global settings instance (safe to import anywhere)
settings = get_settings()
