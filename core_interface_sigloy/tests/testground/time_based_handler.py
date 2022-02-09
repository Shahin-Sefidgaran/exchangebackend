import asyncio
import hashlib
import os
import sys
import time
from datetime import datetime

import aiohttp

START_TIME = time.time()
TOTAL_SLOTS_PER_SEC = 39
EACH_SECOND_CYCLES = 4
PRIORITIES_COUNT = 4  # starts from 1
TOTAL_SLOTS_PER_CYCLE = TOTAL_SLOTS_PER_SEC / EACH_SECOND_CYCLES
CYCLE_DELAY = 1 / EACH_SECOND_CYCLES  # unit is second

CORE_ACCESS_ID = '881D7DBFDCCA4F72AD4469D3F15EBB67'
CORE_SECRET_KEY = '1B53302DDCFB46AD39A3D0753379DD78080F2887D58BEF35'


def custom_print(*args):
    print(*args)


def blockPrint():
    sys.stdout = open(os.devnull, 'w')


def enablePrint():
    sys.stdout = sys.__stdout__


def make_default_slots():
    # round to down always
    slots = [int(TOTAL_SLOTS_PER_CYCLE /
                 PRIORITIES_COUNT)] * int(PRIORITIES_COUNT)
    # add unused slots to the first priority for float results
    diff = int(TOTAL_SLOTS_PER_CYCLE - sum(slots))
    custom_print('diff: ', diff)
    if diff > 0:
        slots[0] += diff
    custom_print('after diff slots:', slots)
    return slots


def make_priorities_counter():
    return [0] * PRIORITIES_COUNT


class RequestManager:
    _waits = {}
    _req_counter = 0
    _extra_slots = 0
    _priorities_slot_portions = make_default_slots()
    _requests_counter_list = make_priorities_counter()
    _cycle_state = 1
    _last_cycle_time = time.time()
    _cycle_full_time = time.time()
    _done = 0

    @staticmethod
    def _sign(params):
        data = '&'.join([key + '=' + str(params[key])
                         for key in sorted(params)])
        data = data + '&secret_key=' + CORE_SECRET_KEY
        data = data.encode()
        return hashlib.md5(data).hexdigest().upper()

    @staticmethod
    async def do_real_req():
        try:
            headers = {
                'Content-Type': 'application/json; charset=utf-8',
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
            }

            url = 'https://api.coinex.com/' + 'perpetual/' + 'v1/' + 'ping'
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    custom_print("Status:", response.status)
                    custom_print("Content-type:",
                                 response.headers['content-type'])
                    res = await response.text()
                    import json
                    js = json.loads(res)
                    custom_print("Body:", js)
                    if "message" in js and js["message"] == "too quick, slow down":
                        custom_print('SLOW DOWN!!!!!!', RequestManager._done)
                        quit()

            # loop = asyncio.get_event_loop()
            # res = await loop.run_in_executor(None, test_cli)
            # if res != "pong":
            #     custom_print('SLOW DOWN!!!!!!', RequestManager._done)
            #     quit()
        except Exception as e:
            print('EXCEPTION!!!! ', e)

    @staticmethod
    async def get_response():
        custom_print('came at: ', datetime.now())
        custom_print('time: ', time.time())
        # await asyncio.sleep(0)
        await RequestManager.do_real_req()
        custom_print('done at: ', time.time())
        RequestManager._done += 1
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
        pr = priority - 1  # starts from zero
        if (not use_extra) and (RequestManager._priorities_slot_portions[pr] > 0):
            RequestManager._priorities_slot_portions[pr] -= 1
            return True
        if use_extra and (RequestManager._extra_slots > 0):
            RequestManager._extra_slots -= 1
            return True
        return False

    @staticmethod
    def go_next_cycle():
        RequestManager._last_cycle_time = time.time()
        # default style
        RequestManager._requests_counter_list = make_priorities_counter()
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
        if (now - RequestManager._last_cycle_time) >= CYCLE_DELAY:
            custom_print('cycle diff:', now - RequestManager._last_cycle_time)
            return True
        return False

    @staticmethod
    def is_last_cycle():
        return RequestManager._cycle_state == PRIORITIES_COUNT

    @staticmethod
    def is_first_cycle():
        return RequestManager._cycle_state == 1

    @staticmethod
    def set_default_priorities():
        # default style
        RequestManager._priorities_slot_portions = make_default_slots()

    @staticmethod
    def add_extra_slots():
        for p in RequestManager._priorities_slot_portions:
            # adds unused slots to extra slots to be used in next cycle
            RequestManager._extra_slots += p

    @staticmethod
    def get_request_delay(priority):
        priority_delay = priority / 1000  # converts to milliseconds
        # delay with preserving requests incoming time
        custom_print(RequestManager._requests_counter_list)

        comming_delay = float(RequestManager._requests_counter_list[priority - 1] /
                              1000000)  # converts to microseconds
        custom_print(CYCLE_DELAY + priority_delay + comming_delay)
        return CYCLE_DELAY + priority_delay + comming_delay

    @staticmethod
    def increase_requests_counter(priority):
        RequestManager._requests_counter_list[priority - 1] += 1

    @staticmethod
    def convert_slots_to_extra():
        RequestManager._extra_slots += sum(
            RequestManager._priorities_slot_portions)
        RequestManager._priorities_slot_portions = [0] * int(PRIORITIES_COUNT)

    @staticmethod
    def time_manager(priority=PRIORITIES_COUNT):
        custom_print('=======================================================')
        RequestManager.increase_requests_counter(priority)
        custom_print('counter: ', RequestManager._requests_counter_list)
        custom_print('slots: ', RequestManager._priorities_slot_portions)
        custom_print('next cycle? ', RequestManager.in_next_cycle())
        custom_print('state:', RequestManager._cycle_state)

        if RequestManager.in_next_cycle():
            cycle = RequestManager.go_next_cycle()
            custom_print('NEXT CYCLE!!!!!!!!! ', cycle)
            RequestManager.add_extra_slots()
            RequestManager.set_default_priorities()

            if RequestManager.is_last_cycle():
                custom_print('THIS IS LAST CYCLE!!!')

                # show be before change slots to default
                RequestManager.convert_slots_to_extra()
            elif RequestManager.is_first_cycle():
                custom_print('THIS IS FIRST CYCLE!!!')
                custom_print('total CYCLE time: ', time.time() -
                             RequestManager._cycle_full_time)
                RequestManager._cycle_full_time = time.time()
                RequestManager._extra_slots = 0

        custom_print('slots2: ', RequestManager._priorities_slot_portions)

        custom_print('extras: ', RequestManager._extra_slots)
        if RequestManager.fill_slot(priority):
            custom_print('slots: ', RequestManager._priorities_slot_portions)
            return 0
        elif RequestManager.fill_slot(priority, use_extra=True):
            custom_print('slots: ', RequestManager._priorities_slot_portions)
            return 0
        else:
            custom_print('slots: ', RequestManager._priorities_slot_portions)
            return RequestManager.get_request_delay(priority)

    @staticmethod
    async def req_sender():
        await asyncio.gather(*[RequestManager.handler() for _ in range(2500)])

    @staticmethod
    async def handler():
        RequestManager._req_counter += 1
        me = RequestManager._req_counter
        tm = time.time()
        wt = RequestManager.time_manager(priority=1)
        while wt > 0:
            custom_print('waiting for: ', wt)
            await asyncio.sleep(wt)
            wt = RequestManager.time_manager(priority=1)

        custom_print('Requesting...')
        resp = await RequestManager.get_response()
        wait_time = time.time() - tm
        custom_print('REQUEST wait time: ', wait_time)
        RequestManager._waits[me] = wait_time
        return resp


async def main():
    await RequestManager.req_sender()
    custom_print(RequestManager._waits)
    custom_print(dict(
        sorted(RequestManager._waits.items(), key=lambda item: item[1])))


asyncio.run(main())
print('START time: ', START_TIME)
custom_print('total time: ', time.time() - START_TIME)
