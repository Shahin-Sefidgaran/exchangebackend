import asyncio
import time
from datetime import datetime

delay = 0.01

START_TIME = time.time()
RESERVE_SLOTS = 3
CHECK_DELAY = 1
TOTAL_SLOTS_PER_SEC = 10
SECOND_CYCLES = 4
PRIORITIES_COUNT = 4
EACH_PRIORITY_PERCENT = 25


class TimeHandler:
    _last_req = time.time()
    _extra_slots = 0
    _second_normal_slots = TOTAL_SLOTS_PER_SEC
    _second_reserved_slots = RESERVE_SLOTS

    @staticmethod
    async def get_response():
        print('came at: ', datetime.now())
        print('time: ', time.time())
        await asyncio.sleep(2)
        print('done at: ', time.time())
        return 0

    @staticmethod
    def wait_time(priority=4):
        if TimeHandler._second_normal_slots > 0:
            TimeHandler._second_normal_slots -= 1
            return 0
        elif TimeHandler._second_reserved_slots > 0:
            TimeHandler._second_reserved_slots -= 1
            return 0
        else:
            pass
        return 1

    @staticmethod
    async def req_sender():
        await asyncio.gather(*[TimeHandler.handler() for _ in range(1000)])

    @staticmethod
    async def handler():
        wt = TimeHandler.wait_time()
        if wt > 0:
            print('waiting for: ', wt)
            await asyncio.sleep(wt)
        resp = await TimeHandler.get_response()
        return resp


async def main():
    await TimeHandler.req_sender()


asyncio.run(main())

print('total time: ', time.time() - START_TIME)
