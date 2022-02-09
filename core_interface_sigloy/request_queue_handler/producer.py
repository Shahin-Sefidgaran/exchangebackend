from request_queue_handler.redis_actions import push


async def producer(data: dict):
    """Produces tasks to the queue to be consumed in consumer"""
    return await push(data)
