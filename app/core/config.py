from pydantic_settings import BaseSettings
from functools import lru_cache
from pydantic import ConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = 'School Task And Attendance System'
    API_V1_STR: str = '/api/v1'
    DATABASE_URL: str

    # --- NEW JWT Settings ---
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    # -- First Super User --
    FIRST_SUPERUSER_EMAIL: str | None = None
    FIRST_SUPERUSER_PASSWORD: str | None = None
    FIRST_SUPERUSER_FULL_NAME: str | None = None
    FIRST_SUPERUSER_ROLL_NUMBER: str | None = None

    model_config = ConfigDict(
        env_file='.env',
        env_file_encoding = 'utf-8'
    )



@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
