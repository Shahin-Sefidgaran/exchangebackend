import time

import pytest
from httpx import AsyncClient

from main import app
from tests.test_constants import BASE_URL


@pytest.mark.asyncio
async def test_ping_route():
    data = {'target_func': 'ping', 'args': {}, 'req_time': time.time()}
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.post("/if", json=data)
    resp_json = response.json()
    assert response.status_code == 200
    assert 'data' in resp_json
    assert resp_json['data']['data'] == 'pong'
