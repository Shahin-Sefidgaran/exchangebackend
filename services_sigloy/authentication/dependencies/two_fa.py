from datetime import datetime, timedelta
from random import randint

import pyotp
from fastapi import Body, Depends, HTTPException
from starlette import status
from starlette.background import BackgroundTask
from starlette.requests import Request

from authentication import models
from authentication.crud import save_verification, get_verification_rec_by_user_id
from authentication.dependencies.auth import get_current_active_user
from authentication.dependencies.token import create_and_save_access_token, create_temp_token
from authentication.models import VerificationTypes
from common.constants import TwoFaCodesStorageTypes
from common.resources import response_strings
from common.schemas import ResponseSchema
from db.pgsql.engine import AsyncDBSession
from db.redis.handler import redis_save, redis_get
from db.redis.namespaces import auth_mail_codes_namespace
from logger.loggers import APP_LOGGER
from logger.tasks import write_log
from mail.handler import send_mail
from mail.shared import MailMessage
from authentication.background_tasks import new_login_happened
from settings import settings


async def create_access_token(request: Request, user: models.User, bg_tasks: BackgroundTask):
    auth_data = await create_and_save_access_token(user)
    bg_tasks.add_task(new_login_happened, request, user)
    
    return auth_data


async def send_2fa_code(user: models.User):
    """Returns user 2fa enabled types and send their codes"""
    # TODO (PHASE 2) check mobile and send its code
    temp_token = await create_temp_token(user)
    if user.two_fa_enabled:
        return ResponseSchema(data={'msg': response_strings.TWO_FA_ACTIVATED,
                                    'tmp_token': temp_token,
                                    'types': '2fa'})
    else:
        await send_verification_mail(user)
        return ResponseSchema(data={'msg': response_strings.TWO_FA_CODE_SENT,
                                    'tmp_token': temp_token,
                                    'types': 'email'})



async def send_verification_mail(user: models.User):
    """Send a verification email to user"""
    code = str(randint(100000, 999999))
    msg = MailMessage(subject="Email Verification",
                      recipients=[user.email],
                      template_body={"code": code},
                      subtype="html")
    await send_mail(msg, 'mail_verification_code.jinja2')
    # save code in db or redis by checking the settings
    if settings.TWO_FA_CODES_STORAGE == TwoFaCodesStorageTypes.DB:
        async with AsyncDBSession() as async_session:
            # save to the db
            await save_verification(async_session, user, VerificationTypes.email_code_verify, code)
    elif settings.TWO_FA_CODES_STORAGE == TwoFaCodesStorageTypes.REDIS:
        await redis_save(auth_mail_codes_namespace, str(user.id), code, settings.TWO_FA_CODES_TIMEOUT)
    else:
        write_log(APP_LOGGER, 'warning', 'mail_verification_sender',
                  f"verification storage type {settings.TWO_FA_CODES_STORAGE} is not implemented.")
        raise NotImplementedError


async def send_mobile_code():
    # TODO (PHASE 2) implement this
    raise NotImplementedError


async def get_email_verification_record_from_db(user: models.User, code) -> models.Verification:
    """Checks the verifications table and get the records for the current user
    with type of 'email_code_verify', iterate over them and check the enter code
     is okay or not, if yes returns that record."""
    async with AsyncDBSession() as async_session:
        user_verification = await get_verification_rec_by_user_id(async_session, user, code,
                                                                  VerificationTypes.email_code_verify)
        if user_verification.created_at <= datetime.now() + timedelta(seconds=settings.TWO_FA_CODES_TIMEOUT):
            return user_verification


async def validate_email_code_from_cache(user: models.User, code) -> bool:
    saved_code = await redis_get(auth_mail_codes_namespace, str(user.id))
    if saved_code is not None and saved_code == code:
        return True
    return False


def verify_totp_code(user, code):
    """Verifies user TOTP code"""
    totp = pyotp.TOTP(user.two_fa_secret_key)
    if not totp.verify(code):
        return False
    return True


def verify_totp_dep(code: str = Body(..., min_length=6, max_length=6, embed=True),
                    current_user: models.User = Depends(get_current_active_user)) -> models.User:
    """Verifies user TOTP code or raise 401 exception"""
    if not verify_totp_code(current_user, code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=response_strings.WRONG_2FA_CODE)
    else:
        return current_user
