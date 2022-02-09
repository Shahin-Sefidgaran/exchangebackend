from celery import Celery

from settings import settings

logger_app = Celery('services_logger', broker=settings.CELERY_BROKER_URL)

logger_app.conf.update(
    timezone='Asia/Tehran',
    enable_utc=True,
)
