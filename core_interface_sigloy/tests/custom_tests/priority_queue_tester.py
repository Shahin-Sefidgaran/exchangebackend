import threading
import time
from random import randint
from time import sleep

import requests

BASE_URL = 'http://localhost:8000'


def request_queue():
    # asset_query
    data = {'target_func': 'ping', 'args': {}, 'req_time': time.time()}
    resp = requests.post(BASE_URL + '/if', json=data)
    print(resp.text)


def p_queue_test():
    while True:
        rng = randint(15, 25)
        print('range: ', rng)
        for i in range(rng):
            t = threading.Thread(target=request_queue)
            t.start()
        sleep(1)


p_queue_test()
