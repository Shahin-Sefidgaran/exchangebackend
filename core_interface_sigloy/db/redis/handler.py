from typing import List

from db.redis.engine import redis


async def redis_save(name_space: str, key: str, val: str, timeout=7200):
    """Save an item to the redis db if "timeout" is not specified, default will be set to
     maximum 2 hours"""
    mixed_key = name_space + ":" + key
    return await redis.set(mixed_key, val, timeout)


async def redis_get(name_space: str, key: str) -> str:
    """Retrieve an item from redis db if exists else none"""
    mixed_key = name_space + ":" + key
    val = await redis.get(mixed_key)
    return val.decode("utf-8") if val else val  # if not "None" convert it to normal string


async def redis_del_key(name_space: str, key):
    """delete key from  the redis"""
    mixed_key = name_space + ":" + key
    return await redis.delete(mixed_key)


async def redis_keys(pattern: str) -> List:
    """Returns a list of keys matching pattern"""
    return [val.decode("utf-8") if val else val for val in await redis.keys(pattern)]
