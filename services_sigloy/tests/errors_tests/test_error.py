import pytest
from httpx import AsyncClient
from starlette.status import HTTP_404_NOT_FOUND

import db.redis.handler
from main import app
from tests.auth_tests.test_auth import BASE_URL


@pytest.mark.asyncio
async def test_http_404_not_found_error():
    async with AsyncClient(base_url=BASE_URL, app=app) as client:
        response = await client.get("/wrong_path/asd")
    assert response.status_code == HTTP_404_NOT_FOUND
    error_data = response.json()
    assert "errors" in error_data
