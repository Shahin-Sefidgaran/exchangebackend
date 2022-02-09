from datetime import datetime
from random import randint

import pyotp
import pytest
from httpx import AsyncClient
from sqlalchemy import select, desc

from authentication import crud, models
from authentication.crud import create_cex_account
from authentication.models import VerificationTypes
from common.constants import TwoFaCodesStorageTypes
from common.utils import unique_string_gen
from db.pgsql.engine import AsyncDBSession
from db.redis.handler import *
from db.redis.namespaces import auth_mail_codes_namespace
from main import app
from settings import settings

# tricky way to handle null responses in json
null = None

BASE_URL = "http://localhost:8080"
username = f"testmail{randint(1111111, 9999999)}@test.com"
password = "test12345"
new_pass = "newpassword_1234"
token = ""
tmp_token = ""
two_fa_types = []

"""This file contains all tests related to the authentication system"""


@pytest.mark.asyncio
async def test_ping():
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"msg": "pong"}


@pytest.mark.asyncio
async def test_register_user_success():
    request_example = {
        "username": username,
        "password": password
    }

    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.post("/auth/register", json=request_example)
    assert response.status_code == 201
    json_response = response.json()
    assert json_response['status'] == 'ok'
    # creates a new free cex account
    async with AsyncDBSession() as async_session:
        await create_cex_account(async_session, email=username, hashed_password=password,
                                 access_id=unique_string_gen(), secret_key=unique_string_gen())


@pytest.mark.asyncio
async def test_register_user_duplicate():
    request_example = {
        "username": username,
        "password": password
    }

    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.post("/auth/register", json=request_example)
    assert response.status_code == 409
    assert response.json()['status'] == 'fail'


@pytest.mark.asyncio
async def test_register_user_validation():
    request_example = {
        "username": 'I Am WRONG Email',
        "password": password
    }
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.post("/auth/register", json=request_example)
    assert response.status_code == 422
    json_response = response.json()
    assert json_response['status'] == 'fail'
    assert "errors" in json_response


async def get_verification_record(type_: VerificationTypes):
    async with AsyncDBSession() as async_session:
        user = await crud.get_user(async_session, username)
        result = await async_session.execute(
            select(models.Verification).filter_by(user_id=user.id, verify_type=type_)
                .order_by(desc(models.Verification.created_at)))
        return result.scalar()


@pytest.mark.asyncio
async def test_verify_registered_mail():
    v_record = await get_verification_record(VerificationTypes.register_email_verify)
    assert v_record
    unique_str = v_record.code
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.get(f"/auth/register/email/verify/{unique_str}")
    assert response.status_code == 200
    assert 'Email verified successfully' in response.text
    assert await get_verification_record(VerificationTypes.register_email_verify) is None


async def first_step_login():
    global tmp_token, two_fa_types, token
    request_example = {
        "username": username,
        "password": password
    }
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.post("/auth/login", data=request_example)
    assert response.status_code == 200
    json_response = response.json()
    if settings.ENABLE_TWO_FA:
        assert json_response['status'] == 'ok'
        assert "tmp_token" in json_response['data']
        tmp_token = json_response['data']['tmp_token']
        two_fa_types = json_response['data']['types']
    else:
        assert json_response['status'] == 'ok'
        assert "access_token" in json_response
        token = json_response['access_token']
        assert "expires_at" in json_response and datetime.fromisoformat(
            json_response['expires_at']) > datetime.now()


@pytest.mark.asyncio
async def test_login_user_first_step():
    await first_step_login()


async def two_step_login():
    global tmp_token, token

    if not settings.ENABLE_TWO_FA:
        return token

    async with AsyncDBSession() as async_session:
        user = await crud.get_user(async_session, username)

        if settings.TWO_FA_CODES_STORAGE == TwoFaCodesStorageTypes.REDIS:
            email_code = await redis_get(auth_mail_codes_namespace, str(user.id))
        elif settings.TWO_FA_CODES_STORAGE == TwoFaCodesStorageTypes.DB:
            v_record = await get_verification_record(VerificationTypes.email_code_verify)
            email_code = v_record.code
        else:
            raise NotImplementedError
    two_fa_code = None
    if '2fa' in two_fa_types:
        two_fa_code = pyotp.totp.TOTP(user.two_fa_secret_key).now()

    request_example = {
        "tmp_token": tmp_token,
        "username": username,
        "password": password,
        "email_code": email_code,
        "two_fa_code": two_fa_code,
    }
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.post("/auth/2fa/verify", json=request_example)
    assert response.status_code == 200
    json_response = response.json()
    assert json_response['status'] == 'ok'
    assert "access_token" in json_response
    token = json_response['access_token']
    assert "expires_at" in json_response and datetime.fromisoformat(
        json_response['expires_at']) > datetime.now()
    assert await get_verification_record(VerificationTypes.email_code_verify) is None
    return token


@pytest.mark.asyncio
async def test_login_user_2fa_email():
    await two_step_login()


@pytest.mark.asyncio
async def test_login_user_fail():
    request_example = {
        "username": username,
        "password": password + 'some wrong letters'
    }
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.post("/auth/login", data=request_example)
    assert response.status_code == 401
    json_response = response.json()
    assert json_response['status'] == 'fail'
    assert "errors" in json_response


@pytest.mark.asyncio
async def test_login_user_validation():
    request_example = {
        "username": 'username.username',
        "password": password + 'some wrong letters' + '0' * 100
    }
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.post("/auth/login", data=request_example)
    assert response.status_code == 401
    json_response = response.json()
    assert json_response['status'] == 'fail'
    assert "errors" in json_response


@pytest.mark.asyncio
async def test_user_info_ok():
    print(token)
    headers = {
        "Authorization": "Bearer " + token
    }
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.get("/auth/me", headers=headers)
    print(response.json())
    assert response.status_code == 200
    json_response = response.json()
    assert json_response['status'] == 'ok'
    assert json_response['data']['username'] == username


@pytest.mark.asyncio
async def test_user_info_fail():
    headers = {
        "Authorization": "Bearer " + token + 'some wrong string'
    }
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.get("/auth/me", headers=headers)
    assert response.status_code == 401
    json_response = response.json()
    assert json_response['status'] == 'fail'


@pytest.mark.asyncio
async def test_change_password_success():
    headers = {
        "Authorization": "Bearer " + token
    }
    request_example = {
        "password": password,
        "new_passwords": {
            "new_password": new_pass,
            "new_password_confirm": new_pass
        }
    }
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.patch("/auth/password", headers=headers, json=request_example)

        assert response.status_code == 200
        json_response = response.json()
        assert json_response['status'] == 'ok'
        assert "data" in json_response

        # confirming password changing and turn password to last one again
        request_example = {
            "password": new_pass,
            "new_passwords": {
                "new_password": password,
                "new_password_confirm": password
            }
        }
        response = await ac.patch("/auth/password", headers=headers, json=request_example)

        assert response.status_code == 200
        json_response = response.json()
        assert json_response['status'] == 'ok'
        assert "data" in json_response


@pytest.mark.asyncio
async def test_change_password_fail():
    headers = {
        "Authorization": "Bearer " + token
    }
    request_example = {
        "password": password + 'some wrong string',
        "new_passwords": {
            "new_password": password + '123',
            "new_password_confirm": password + '123'
        }
    }
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.patch("/auth/password", headers=headers, json=request_example)

    json_response = response.json()
    assert response.status_code == 401
    assert json_response['status'] == 'fail'
    assert "errors" in json_response


@pytest.mark.asyncio
async def test_change_password_validation():
    headers = {
        "Authorization": "Bearer " + token
    }
    request_example = {
        "password": 'lttl',
        "new_passwords": {
            "new_password": 'lttl',  # little string
            "new_password_confirm": 'lttl'
        }
    }
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.patch("/auth/password", headers=headers, json=request_example)

    json_response = response.json()
    assert response.status_code == 422
    assert json_response['status'] == 'fail'
    assert "errors" in json_response


@pytest.mark.asyncio
async def test_preactive_two_fa():
    headers = {
        "Authorization": "Bearer " + token
    }

    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.get("/auth/2fa/activate", headers=headers)
    assert response.status_code == 200
    assert 'uri' in response.json()['data']


@pytest.mark.asyncio
async def test_active_two_fa():
    headers = {
        "Authorization": "Bearer " + token
    }

    async with AsyncDBSession() as async_session:
        user = await crud.get_user(async_session, username)

    code = pyotp.totp.TOTP(user.two_fa_secret_key).now()
    request_example = {
        "code": code,
    }
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.post("/auth/2fa/activate", headers=headers, json=request_example)

        assert response.status_code == 200
        json_response = response.json()
        assert json_response['status'] == 'ok'
        assert "data" in json_response


@pytest.mark.asyncio
async def test_auth_db():
    async with AsyncDBSession() as async_session:
        user = await crud.get_user(async_session, username)
    assert user.token == token


@pytest.mark.asyncio
async def test_login_history():
    headers = {
        "Authorization": "Bearer " + token
    }
    page_counter = 0
    while True:
        async with AsyncClient(app=app, base_url=BASE_URL) as ac:
            response = await ac.get(f"/auth/history/{page_counter}", headers=headers)
        json_resp = response.json()
        assert response.status_code == 200
        assert len(json_resp) <= 5
        if page_counter == 0:
            assert len(json_resp) != 0

        for i in json_resp:
            assert i['ip']
            assert i['created_at']

        if len(json_resp) == 0:
            break
        page_counter += 1


@pytest.mark.asyncio
async def test_logout():
    headers = {
        "Authorization": "Bearer " + token
    }

    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.get("/auth/logout", headers=headers)
    assert response.status_code == 200

    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.get("/auth/me", headers=headers)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_user_first_step_again():
    await first_step_login()


@pytest.mark.asyncio
async def test_login_user_2fa():
    await two_step_login()


@pytest.mark.asyncio
async def test_deactive_two_fa():
    headers = {
        "Authorization": "Bearer " + token
    }

    async with AsyncDBSession() as async_session:
        user = await crud.get_user(async_session, username)

    code = pyotp.totp.TOTP(user.two_fa_secret_key).now()
    request_example = {
        "code": code,
    }
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.post("/auth/2fa/deactivate", headers=headers, json=request_example)

        assert response.status_code == 200
        json_response = response.json()
        assert json_response['status'] == 'ok'
        assert "data" in json_response

    await first_step_login()

    assert '2fa' not in two_fa_types


@pytest.mark.asyncio
async def test_forget_form():
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.get("/auth/forget/form")
    assert response.status_code == 200
    json_response = response.json()
    assert 'data' in json_response
    size = len(json_response['data'])
    assert size

    headers = {
        "Authorization": "Bearer " + token
    }
    answers = ['ksajdfkskf'] * size
    request_example = {
        'username': username,
        "answers": ','.join(answers)
    }
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.post("/auth/forget/form", headers=headers, data=request_example)
    assert response.status_code == 200
    json_response = response.json()
    assert 'status' in json_response
    assert json_response['status'] == 'ok'


@pytest.mark.asyncio
async def test_forget_reset_password():
    global two_fa_types
    global tmp_token

    request_example = {
        'username': username,
    }
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.post("/auth/2fa/get_code", json=request_example)
    assert response.status_code == 200
    resp_json = response.json()
    assert 'tmp_token' in resp_json['data']
    assert 'types' in resp_json['data']
    two_fa_types = resp_json['data']['types']
    tmp_token = resp_json['data']['tmp_token']

    async with AsyncDBSession() as async_session:
        user = await crud.get_user(async_session, username)

        if settings.TWO_FA_CODES_STORAGE == TwoFaCodesStorageTypes.REDIS:
            email_code = await redis_get(auth_mail_codes_namespace, str(user.id))
        elif settings.TWO_FA_CODES_STORAGE == TwoFaCodesStorageTypes.DB:
            v_record = await get_verification_record(VerificationTypes.email_code_verify)
            email_code = v_record.code
        else:
            raise NotImplementedError

    two_fa_code = None
    if '2fa' in two_fa_types:
        two_fa_code = pyotp.totp.TOTP(user.two_fa_secret_key).now()

    request_example = {
        "tmp_token": tmp_token,
        "username": username,
        "new_passwords": {
            "new_password": password,
            "new_password_confirm": password
        },
        "email_code": email_code,
        "two_fa_code": two_fa_code,
    }

    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.post("/auth/forget/reset_password", json=request_example)
    assert response.status_code == 200
    json_response = response.json()
    assert json_response['status'] == 'ok'
    assert await get_verification_record(VerificationTypes.email_code_verify) is None
