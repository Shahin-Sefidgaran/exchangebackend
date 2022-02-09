import asyncio
import time

import aiohttp


class SlowDownException(Exception):
    pass


START_TIME = time.time()
TOTAL_SECS = 250
req_per_sec = 22
stop = False


# def ping():
#     headers = {
#         'Content-Type': 'application/json; charset=utf-8',
#         'Accept': 'application/json',
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
#                       'Chrome/60.0.3112.90 Safari/537.36 '
#     }
#
#     url = 'https://api.coinex.com/' + 'perpetual/' + 'v1/' + 'ping'
#     resp = requests.get(url, headers=headers)
#     res = resp.text
#     import json
#     js = json.loads(res)
#     print(js)
#     if "message" in js and js["message"] == "too quick, slow down":
#         print('SLOW DOWN!!!!!!')
#         raise SlowDownException
#
#
# def rps_checker_v1():
#     while True:
#         next_sec = time.time() + 1
#         main_threads = []
#
#         for _ in range(req_per_sec):
#             t = threading.Thread(target=ping)
#             main_threads.append(t)
#
#         for t in main_threads:
#             print(f'time: ', time.time())
#             time.sleep(0.015)
#             t.start()
#
#         print('sleeping for: ', next_sec - time.time())
#         time.sleep(next_sec - time.time() if next_sec - time.time() > 0 else 0)
#
#
# while True:
#     try:
#         rps_checker_v1()
#     except SlowDownException:
#         print('sleeping for 3 mins:')
#         time.sleep(180)
#         req_per_sec -= 1

async def rps_checker_v2():
    global stop, req_per_sec
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
    }

    url = 'https://api.coinex.com/' + 'perpetual/' + 'v1/' + 'ping'
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            res = await response.text()
            import json
            js = json.loads(res)
            print(js)
            if "message" in js and js["message"] == "too quick, slow down":
                print('SLOW DOWN!!!!!!')
                stop = True


async def main():
    global req_per_sec, stop
    while True:
        print('rps:', req_per_sec)
        next_sec = time.time() + 1
        if stop:
            req_per_sec -= 1
            print('sleeping for 3 mins: ')
            await asyncio.sleep(180)
            stop = False
            continue
        if not stop:
            for _ in range(req_per_sec):
                asyncio.create_task(rps_checker_v2())
                await asyncio.sleep(0.015)
                if next_sec <= time.time() or stop:
                    break
        print('sleeping for: ', next_sec - time.time())
        await asyncio.sleep(next_sec - time.time() if next_sec - time.time() > 0 else 0)


asyncio.run(main())
