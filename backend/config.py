from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    APP_NAME: str = "AetherMesh Runtime"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    GEMINI_API_KEY: str = Field(default="")
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
settings = get_settings()