from datetime import timedelta, datetime

from jose import jwt

from authentication import models, crud
from common.utils import unique_string_gen
from db.pgsql.engine import AsyncDBSession
from db.redis.handler import redis_save, redis_get
from db.redis.namespaces import auth_temp_token_namespace
from settings import settings


def create_access_token(data: dict):
    """Create an access token using jwt lib"""
    to_encode = data.copy()
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def get_token_expire_time():
    expires_delta = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return datetime.now() + expires_delta  # token expire time


async def create_temp_token(user: models.User):
    temp_token = unique_string_gen()
    await redis_save(auth_temp_token_namespace, str(user.id), temp_token, settings.AUTH_TEMP_TOKEN_TIMEOUT)
    return temp_token


async def validate_temp_token(user: models.User, token):
    temp_token = await redis_get(auth_temp_token_namespace, str(user.id))
    if temp_token is not None and temp_token == token:
        return True
    return False


async def create_and_save_access_token(user: models.User):
    # create access token
    expires_at = get_token_expire_time()
    access_token = create_access_token(data={"sub": user.username,
                                             "exp": expires_at.timestamp()})
    async with AsyncDBSession() as async_session:
        await crud.update_user(async_session, user, use_orm=False, token=access_token,
                               token_expires_at=expires_at)
    data = {"status": "ok", "access_token": access_token,
            "token_type": "bearer", "expires_at": str(expires_at)}
    return data


async def delete_token(user: models.User):
    async with AsyncDBSession() as async_session:
        await crud.update_user(async_session, user, use_orm=False, token="")
