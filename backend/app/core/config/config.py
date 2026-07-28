from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "SalesLens AI"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Auth
    SECRET_KEY: str = "change_this_to_a_secure_random_string_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Models & Services
    LITELLM_API_BASE: str = "http://localhost:4000"  # Default LiteLLM proxy
    DEFAULT_MODEL: str = "llama-3-8b"
    
    # Langfuse
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_BASE_URL: str = "https://cloud.langfuse.com"
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
