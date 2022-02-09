from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str
    DEBUG: bool
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    MIGRATE_ON_START: bool
    SQLALCHEMY_DATABASE_URL: str
    CORE_URL: str
    SERVICES_URL: str
    CORE_HANDLER_URI: str
    CURRENCY_HANDLER_URI: str
    CORE_STORE_KEYS_URI: str
    CORE_UPDATE_KEYS_URI: str
    CORE_REQUEST_TIMEOUT: int
    ENABLE_LOGGING: bool
    LOG_ARCHIVE_INTERVAL: str
    CELERY_BROKER_URL: str
    WRITE_CELERY_LOGS_TO_FILE: bool
    MONGODB_URL: str
    RATE_LIMITER_REDIS_URL: str
    REDIS_URL: str
    TWO_FA_CODES_STORAGE: str
    AUTH_TEMP_TOKEN_TIMEOUT: int
    TWO_FA_CODES_TIMEOUT: int
    TOKEN_URL: str
    ENABLE_TWO_FA: bool
    ENABLE_USER_CACHING: bool
    NOTIFICATION_TOKEN_TIMEOUT: int
    NOTIFICATION_QUEUE_LIFETIME: int
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_FROM_NAME: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_TLS: bool
    MAIL_SSL: bool
    USE_CREDENTIALS: bool
    VALIDATE_CERTS: bool
    TEMPLATE_FOLDER: str
    CONVERT_FEE: float

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
