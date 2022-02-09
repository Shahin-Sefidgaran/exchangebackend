import json

from db.redis.engine import redis
from settings import settings


async def push(queue_name: str, data: dict) -> None:
    """pushes data to the handler queue"""
    encoded = json.dumps(data)
    # pushes item to it's specific queue
    await redis.lpush(queue_name, encoded)
    # delete item from the queue after this timeout
    await redis.expire(queue_name, settings.NOTIFICATION_QUEUE_LIFETIME)


async def pop(queue_name: str):
    """pops data from the handler queue"""
    value = await redis.rpop(queue_name)
    if value is not None:
        return json.loads(value)
