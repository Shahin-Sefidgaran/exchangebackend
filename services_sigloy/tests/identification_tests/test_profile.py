import pytest
from httpx import AsyncClient

from main import app
from tests.auth_tests.test_auth import first_step_login, two_step_login, BASE_URL

token = ""


@pytest.mark.asyncio
async def test_login_user_first_step():
    await first_step_login()


@pytest.mark.asyncio
async def test_login_user_2fa_email():
    global token
    token = await two_step_login()
    assert token


@pytest.mark.asyncio
async def test_user_info():
    headers = {
        "Authorization": "Bearer " + token
    }
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.get("/profile/info", headers=headers)
    json_resp = response.json()
    assert response.status_code == 200
    assert 'data' in json_resp
    assert "first_name" in json_resp['data']
    assert json_resp['data']['first_name'] is None


@pytest.mark.asyncio
async def test_set_user_info():
    headers = {
        "Authorization": "Bearer " + token
    }
    test_file = open('tests/identification_tests/test_img.jpg', 'rb')
    data = {
        'first_name': "test name"
    }
    files = {'id_image': test_file}
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.put("/profile/info", data=data, files=files, headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_user_info():
    headers = {
        "Authorization": "Bearer " + token
    }
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.get("/profile/info", headers=headers)
    json_resp = response.json()
    assert response.status_code == 200
    assert 'data' in json_resp
    assert "first_name" in json_resp['data']
    assert json_resp['data']['first_name'] == 'test name'
    assert json_resp['data']['id_image'] is not None
