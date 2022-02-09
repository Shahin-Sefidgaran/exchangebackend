import threading
from random import randint

import requests

base_url = "http://localhost:8000"
ping_url = '/ping'

ping_threads = 100
main_request_threads = 100


def login_test(n):
    res = requests.post(
        base_url + '/auth/login',
        data={'username': f'testtt-{n}@gmail.com', 'password': 'test1234'})
    print(res.text)


def register_test(n):
    rand_n = randint(0, 1000)
    rand_n1 = randint(0, 1000)
    res = requests.post(
        base_url + '/auth/register',
        # json={'username': f'{rand_n}testtt-{n}-{rand_n1}@gmail.com', 'password': 'test1234'})
        json={'username': f'testtt-{n}@gmail.com', 'password': 'test1234'})
    print(res.text)


def ping_test():
    res = requests.get(base_url + ping_url)
    print(res.text)


def main():
    main_threads = []
    for i in range(main_request_threads):
        t = threading.Thread(target=register_test, args=(i,))
        main_threads.append(t)

    for t in main_threads:
        t.start()
    # ============================================================
    ping_threads = []
    for i in range(ping_threads):
        t = threading.Thread(target=ping_test)
        ping_threads.append(t)

    for t in ping_threads:
        t.start()
