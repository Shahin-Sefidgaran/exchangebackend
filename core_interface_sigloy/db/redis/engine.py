import aioredis

# REDIS SECTION
from settings import settings

REDIS_QUEUE_TIMEOUT = 60

redis = aioredis.from_url(settings.REDIS_URL)
