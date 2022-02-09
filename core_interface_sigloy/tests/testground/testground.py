import asyncio
import time
from datetime import datetime

delay = 0.01

START_TIME = time.time()
TOTAL_SLOTS_PER_SEC = 40
EACH_SECOND_CYCLES = 4
PRIORITIES_COUNT = 4  # starts from 1
CYCLE_DELAY = 1 / EACH_SECOND_CYCLES  # unit is second
DEFAULT_PRIORITY_SLOTS = [TOTAL_SLOTS_PER_SEC /
                          PRIORITIES_COUNT] * PRIORITIES_COUNT


class RequestManager:
    _extra_slots = 0
    _priorities_slot_portions = DEFAULT_PRIORITY_SLOTS
    _cycle_slots = TOTAL_SLOTS_PER_SEC / PRIORITIES_COUNT
    _cycle_state = 1
    _last_cycle_time = time.time()
    _requests_counter = 0

    @staticmethod
    async def get_response():
        print('came at: ', datetime.now())
        print('time: ', time.time())
        await asyncio.sleep(2)
        print('done at: ', time.time())
        return 0

    @staticmethod
    def fill_slot(priority, use_extra=False):
        """
        First checks is there any free slot in normal and extra slots then fills it.
        Args:
            priority (int): priority of the request
        Returns:
            Bool 
        """
        # checks is there any available slots or not
        if (not use_extra) and (RequestManager._priorities_slot_portions[priority] > 0):
            RequestManager._priorities_slot_portions[priority] -= 1
            return True
        if use_extra and (RequestManager._extra_slots > 0):
            RequestManager._extra_slots -= 1
            return True
        return False

    @staticmethod
    def go_next_cycle():
        RequestManager._last_cycle_time = time.time()
        RequestManager._requests_counter = 0
        if RequestManager.is_last_cycle():
            RequestManager._cycle_state = 1
        else:
            RequestManager._cycle_state += 1
        return RequestManager._cycle_state

    @staticmethod
    def in_next_cycle():
        """
        Checks we are in the next cycle by checking time
        """
        now = time.time()
        if (now - RequestManager._last_cycle_time) > CYCLE_DELAY:
            return True
        return False

    @staticmethod
    def is_last_cycle():
        return RequestManager._cycle_state == EACH_SECOND_CYCLES

    @staticmethod
    def is_first_cycle():
        return RequestManager._cycle_state == 1

    @staticmethod
    def set_default_priorities():
        RequestManager._priorities_slot_portions = DEFAULT_PRIORITY_SLOTS

    @staticmethod
    def add_extra_slots():
        for p in RequestManager._priorities_slot_portions:
            # adds unused slots to extra slots to be used in next cycle
            RequestManager._extra_slots += p

    @staticmethod
    def get_request_delay(priority):
        priority_delay = priority / 1000  # converts to milliseconds
        # delay with preserving requests incoming time
        comming_delay = RequestManager._requests_counter / \
                        10000000000  # converts to nanoseconds
        return CYCLE_DELAY + priority_delay + comming_delay

    @staticmethod
    def time_manager(priority=PRIORITIES_COUNT):
        RequestManager._requests_counter += 1

        if RequestManager.in_next_cycle:
            RequestManager.go_next_cycle()
            if RequestManager.is_last_cycle:
                RequestManager.add_extra_slots()
            if RequestManager.is_first_cycle():
                RequestManager._extra_slots = 0
            RequestManager.set_default_priorities()

        if RequestManager.fill_slot(priority):
            return 0
        elif RequestManager.fill_slot(priority, use_extra=True):
            return 0
        else:
            return RequestManager.get_request_delay(priority)

    @staticmethod
    async def req_sender():
        await asyncio.gather(*[RequestManager.handler() for _ in range(1000)])

    @staticmethod
    async def handler():
        wt = RequestManager.time_manager()
        if wt > 0:
            print('waiting for: ', wt)
            await asyncio.sleep(wt)
        resp = await RequestManager.get_response()
        return resp


async def main():
    await RequestManager.req_sender()


asyncio.run(main())

print('total time: ', time.time() - START_TIME)
