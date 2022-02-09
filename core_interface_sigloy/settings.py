from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str
    DEBUG: bool
    SECRET_KEY: str
    CORE_ACCESS_ID: str
    CORE_SECRET_KEY: str
    MIGRATE_ON_START: bool
    SQLALCHEMY_DATABASE_URL: str
    TOTAL_REQUESTS_PER_SECOND: int
    REQUESTS_QUEUE_NAME: str
    REDIS_URL: str
    REDIS_KEYS_TIMEOUT: int
    REQUEST_TIMEOUT: int
    DEFAULT_PRIORITY: int
    DELAY_BETWEEN_REQUESTS: float
    ENABLE_LOGGING: bool
    LOG_ARCHIVE_INTERVAL: str
    CELERY_BROKER_URL: str
    WRITE_CELERY_LOGS_TO_FILE: bool

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
