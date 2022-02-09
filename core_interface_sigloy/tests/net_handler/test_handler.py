import asyncio
import time

import pytest
from httpx import AsyncClient

from main import app
from settings import settings
from tests.test_constants import BASE_URL


async def sender_and_check():
    data = {'target_func': 'ping', 'args': {}, 'req_time': time.time()}
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.post("/if", json=data)
    resp_json = response.json()
    assert response.status_code == 200
    assert 'data' in resp_json
    assert resp_json['data']['data'] == 'pong'


@pytest.mark.asyncio
async def test_request_handler():
    number_of_requests = 100
    start_time = time.time()
    await asyncio.gather(*[sender_and_check() for _ in range(number_of_requests)])
    wait_time = number_of_requests / settings.TOTAL_REQUESTS_PER_SECOND + 1  # +1 is taking time for response
    elapsed = time.time() - start_time
    assert elapsed <= wait_time
