import asyncio
import time
from queue import Empty, PriorityQueue

from core.core_api import CoreApi
from core.endpoints_priorities import priorities
from logger.loggers import QUEUE_LOGGER
from logger.tasks import write_log
from request_queue_handler.queue_items import PrioritizedItem
from request_queue_handler.redis_actions import pop
from request_queue_handler.request_wrapper import RequestWrapper
from settings import settings

total_rps = settings.TOTAL_REQUESTS_PER_SECOND
QUEUE_EMPTY_SLEEP = 0.1

# script's internal heap queue (lower priority is more important) !!
q = PriorityQueue()


def get_item_priority(payload):
    """Gets priority of each request and return the priority"""
    target_func = payload['data']['target_func']
    function_ = CoreApi.get_class_operation(target_func)
    if function_ in priorities:
        return priorities[function_]
    else:
        return settings.DEFAULT_PRIORITY


async def redis_consumer():
    """Gets items from the redis queue and put them in
        internal python build-in priority queue"""
    while True:
        data = await pop()
        if data is not None:
            write_log(QUEUE_LOGGER, 'debug', 'redis consumer',
                      f'new item found: {data}')
            priority = get_item_priority(data)
            p_item = PrioritizedItem(priority, data, float(data['data']['req_time']))
            q.put_nowait(p_item)
        else:
            await asyncio.sleep(QUEUE_EMPTY_SLEEP)


async def internal_consumer():
    """Consume internal queue to send requests to the "Core" """
    while True:
        next_second = time.time() + 1
        try:
            counter = 0
            while counter < total_rps:
                item: PrioritizedItem = q.get_nowait()
                write_log(QUEUE_LOGGER, 'info', 'internal consumer',
                          f'current queue size: {q.qsize()}')
                if item.is_timed_out():
                    continue
                else:
                    write_log(QUEUE_LOGGER, 'debug', 'internal consumer',
                              f'received item data: {item}')
                    wrapper = RequestWrapper(req_id=item.data['id'], data=item.data['data'])
                    asyncio.create_task(wrapper.send())
                    counter += 1

                if next_second <= time.time():
                    break

                # very small sleep to prevent connection creation blocks
                await asyncio.sleep(settings.DELAY_BETWEEN_REQUESTS)
        except Empty:
            await asyncio.sleep(QUEUE_EMPTY_SLEEP)
            continue
        until_next_sec = (next_second - time.time()) if (next_second - time.time()) > 0 else 0
        await asyncio.sleep(until_next_sec)


async def run_consumers():
    """Running consumers in async loop"""
    write_log(QUEUE_LOGGER, 'info', 'run consumers', 'starting consumers...')
    await asyncio.gather(*[redis_consumer(), internal_consumer()])


def main():
    asyncio.run(run_consumers())
