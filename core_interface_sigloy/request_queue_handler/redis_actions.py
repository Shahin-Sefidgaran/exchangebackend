import json

from db.redis.engine import redis
from db.redis.handler import redis_save, redis_get
from settings import settings


async def push(data: dict):
    """pushes data to the handler queue"""
    encoded = json.dumps(data)
    return await redis.lpush(settings.REQUESTS_QUEUE_NAME, encoded)


async def pop():
    """pops data from the handler queue"""
    value = await redis.rpop(settings.REQUESTS_QUEUE_NAME)
    if value is not None:
        return json.loads(value)


async def get_result(namespace: str, key: str):
    """get results from the redis"""
    value = await redis_get(namespace, key)
    if value is not None:
        return json.loads(value)


async def put_result(namespace: str, key: str, result: dict):
    """set results to the redis"""
    encoded = json.dumps(result)
    return await redis_save(namespace, key, encoded, settings.REDIS_KEYS_TIMEOUT)


