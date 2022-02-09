import time
from uuid import uuid4


def epoch_milliseconds():
    return int(time.time() * 1000)


def unique_id():
    return uuid4()
