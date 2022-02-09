import json
from datetime import datetime

from aiohttp import ClientError, ClientResponseError
from fastapi import Body
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import EmailStr
from starlette import status
from starlette.requests import Request

from authentication import crud, models
from authentication.crud import save_verification
from authentication.dependencies.password import verify_password, get_password_hash
from authentication.dependencies.token import create_access_token, get_token_expire_time
from authentication.models import UserStatuses, VerificationTypes
from authentication.schemas import UserRegister, UserScheme
from common.helpers import sync_to_async
from common.resources import response_strings
from common.utils import unique_string_gen
from core_router.network import if_http_request
from db.pgsql.engine import AsyncDBSession
from db.redis.handler import redis_get, redis_save
from db.redis.namespaces import auth_userinfo_namespace
from logger.loggers import NETWORK_LOGGER, APP_LOGGER, DB_LOGGER
from logger.tasks import write_log
from mail.handler import send_mail
from mail.shared import MailMessage
from settings import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.TOKEN_URL)


async def get_user_from_cache(username: str) -> models.User:
    user_info = await redis_get(auth_userinfo_namespace, username)
    if user_info:
        user_info = json.loads(user_info)
        # Converts it to UserInfo pydantic class to initiate columns types,
        # then converts it to models.User object
        user_info = UserScheme(**user_info)  # Pydantic schema
        user = models.User(**user_info.dict())  # User model
        return user


async def save_user_to_cache(user: models.User):
    user_info_json = UserScheme.from_orm(user).json()
    await redis_save(auth_userinfo_namespace, user.username, user_info_json)


async def get_user(username: str, async_session=None) -> models.User:
    """Return current user by its username, if "async_session" parameter specified,
     gets user from database else first tries to get it from cache if user information
     is not exist in cache sends a database query. Usually use this function for read purposes."""
    # Save and get from redis users
    if async_session:
        return await crud.get_user(async_session, username)
    else:
        write_log(DB_LOGGER, 'info', 'get user function', f'tries to get user {username} from cache.')
        user = await get_user_from_cache(username)
        if not user or not settings.ENABLE_USER_CACHING:
            async with AsyncDBSession() as async_session:
                user = await crud.get_user(async_session, username)
                if user and settings.ENABLE_USER_CACHING:
                    await save_user_to_cache(user)
        return user  # returns models.User or None


async def authenticate_user(username: str, password: str, async_session=None):
    """Checks the password is correct or not"""
    user = await get_user(username, async_session)
    if user and await sync_to_async(verify_password, password, user.hashed_password):
        return user


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Gets current user by using "Token" in header """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=response_strings.INVALID_CREDENTIALS,
        headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, settings.SECRET_KEY,
                             algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await get_user(username=username)
    # TODO (PHASE 2) for login with multiple devices here should be changed
    # check token is user's current token and it's expire time
    if user is None or token != user.token or user.token_expires_at <= datetime.now():
        raise credentials_exception
    return user


async def get_current_active_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    """Get user and check is it activate or not"""
    if current_user.status == models.UserStatuses.inactive:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail={"msg": response_strings.INACTIVE_USER})
    return current_user


async def create_user_or_fail(new_user: UserRegister) -> models.User:
    """username is email for now... """
    user = await get_user(username=new_user.username)
    if user:
        if user.status == UserStatuses.not_verified:
            return user
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail={"msg": response_strings.USER_EXISTS})
    hashed_password = await sync_to_async(get_password_hash, new_user.password)
    expires_at = get_token_expire_time()
    access_token = await sync_to_async(create_access_token,
                                       data={"sub": new_user.username, "exp": expires_at.timestamp()})
    async with AsyncDBSession() as async_session:
        created_user = await crud.create_user(async_session, email=new_user.username, token=access_token,
                                              token_expires_at=expires_at,
                                              username=new_user.username, hashed_password=hashed_password)
        return created_user


async def send_keys_to_if(user_id, access_id, secret_key, update=False):
    """Save or update keys to the interface"""
    if update:
        url = settings.CORE_URL + settings.CORE_UPDATE_KEYS_URI
    else:
        url = settings.CORE_URL + settings.CORE_STORE_KEYS_URI
    data = {'user_id': user_id, 'access_id': access_id, 'secret_key': secret_key}
    try:
        response = await if_http_request(url, 'post', data)
        if response['status'] == 'ok':
            return True
        else:
            write_log(NETWORK_LOGGER, 'warning', 'key sender',
                      f'sending keys to if received failed, response:{response}')
            return True
    except ClientError or ClientResponseError as e:
        write_log(APP_LOGGER, 'warning', 'verify email route',
                  f"couldn't send keys to interface successfully for user {user_id}. reason: {e}")
        return False


async def get_user_by_username(username: EmailStr = Body(...)):
    """Return user by using username or NONE"""
    user = await get_user(username)
    if user:
        if user.status == UserStatuses.inactive:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=response_strings.ACCOUNT_IS_BANNED)
        if user.status == UserStatuses.not_verified:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail=response_strings.ACCOUNT_IS_NOT_VERIFIED)
        return user
    else:
        return None


def check_user_password(user: models.User = Depends(get_current_active_user),
                        # TODO (PHASE 2) change password policies later
                        password: str = Body(..., min_length=8, max_length=50)) -> models.User:
    # we do not check users current password is the same as the current password or not
    # because of it's time consuming verify algorithm, this is a tradeoff between db tx
    # and cpu processing
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail={"msg": response_strings.INCORRECT_CURRENT_PASSWORD})

    # if the password is correct, returns the user
    return user


async def send_register_verification_mail(request: Request, user: models.User):
    """Send a verification email for a registered user"""
    unique_string = unique_string_gen()  # 32 bit string
    verify_link = request.url_for('verify_email', unique_id=unique_string)
    msg = MailMessage(subject="Registration",
                      recipients=[user.email],
                      template_body={"link": verify_link},
                      subtype="html")
    await send_mail(msg, 'register_verify.jinja2')
    async with AsyncDBSession() as async_session:
        # save to the db
        await save_verification(async_session, user, VerificationTypes.register_email_verify, unique_string)
