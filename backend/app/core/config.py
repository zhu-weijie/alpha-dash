# backend/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "alpha-dash"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    # model_config is the Pydantic V2 way to configure model behavior
    model_config = SettingsConfigDict(
        env_file=".env",      # Specifies the .env file to load
        extra="ignore"        # Ignores extra fields found in the environment or .env file
    )

@lru_cache() # Caches the result of get_settings() for performance
def get_settings():
    return Settings()

settings = get_settings() # Make settings instance available for import elsewhere
