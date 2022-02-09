import pytest
from httpx import AsyncClient

from db.pgsql.engine import AsyncDBSession
from main import app
from notification import crud
from tests.auth_tests.test_auth import first_step_login, two_step_login, BASE_URL

token = ""
notification_token = ""
notification_id = -1
""" !! Notification websocket test is not here and should be tested handily !! """


class DebugIsOffException(Exception):
    pass


@pytest.mark.asyncio
async def test_login():
    global token
    await first_step_login()
    token = await two_step_login()
    assert token


@pytest.mark.asyncio
async def test_websocket_temp_token():
    global notification_token
    headers = {
        "Authorization": "Bearer " + token
    }
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.get("/notification/token", headers=headers)
    json_resp = response.json()
    assert response.status_code == 200
    assert 'data' in json_resp
    assert "temp_token" in json_resp['data']
    notification_token = json_resp['data']['temp_token']


async def send_notification():
    global notification_id
    headers = {
        "Authorization": "Bearer " + token
    }
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.get("/notification/notify", headers=headers)
    if response.status_code == 404:
        raise DebugIsOffException('Change "DEBUG" to "True" in ".env" file then run this test.')
    json_resp = response.json()
    assert response.status_code == 200
    assert 'data' in json_resp
    assert 'notification_id' in json_resp['data']
    notification_id = json_resp['data']['notification_id']
    async with AsyncDBSession() as async_session:
        notification_record = await crud.get_notification(async_session, notification_id)
    assert not notification_record.read
    return notification_id


@pytest.mark.asyncio
async def test_new_notification1():
    await send_notification()


@pytest.mark.asyncio
async def test_websocket_read_notification():
    global notification_id
    headers = {
        "Authorization": "Bearer " + token
    }
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.get(f"/notification/read/{notification_id}", headers=headers)
    assert response.status_code == 200
    async with AsyncDBSession() as async_session:
        notification_record = await crud.get_notification(async_session, notification_id)
    assert notification_record.read


@pytest.mark.asyncio
async def test_new_notification2():
    await send_notification()


@pytest.mark.asyncio
async def test_websocket_read_all_notifications():
    global notification_id
    headers = {
        "Authorization": "Bearer " + token
    }
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.get(f"/notification/read/{notification_id}", headers=headers)
    assert response.status_code == 200
    async with AsyncDBSession() as async_session:
        notification_record = await crud.get_notification(async_session, notification_id)
    assert notification_record.read


@pytest.mark.asyncio
async def test_get_new_notification():
    global notification_id
    headers = {
        "Authorization": "Bearer " + token
    }
    page_counter = 0
    while True:
        async with AsyncClient(app=app, base_url=BASE_URL) as ac:
            response = await ac.get(f"/notification/news/{page_counter}", headers=headers)
        json_resp = response.json()
        assert response.status_code == 200
        assert len(json_resp) <= 5
        if page_counter == 0:
            assert len(json_resp) != 0

        for i in json_resp:
            assert i['data']
            assert i['created_at']

        if len(json_resp) == 0:
            break
        page_counter += 1
