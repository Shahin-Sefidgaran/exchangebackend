from slowapi import Limiter
from slowapi.util import get_remote_address

from settings import settings

# need to pas "request: Request" as first argument after decorator
limiter = Limiter(key_func=get_remote_address
                  # TODO (DEPLOY) uncomment this in production
                  # , storage_uri=settings.RATE_LIMITER_REDIS_URL
                  )
