import json
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Depends, Body, HTTPException
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.background import BackgroundTasks

from authentication import crud, models
from authentication.background_tasks import delete_unused_verification, notify_password_changed
from authentication.dependencies.auth import get_user_by_username
from authentication.dependencies.forget import get_answers_dict
from authentication.dependencies.password import hash_new_password
from authentication.dependencies.token import validate_temp_token, delete_token
from authentication.dependencies.two_fa import get_email_verification_record_from_db, verify_totp_code, \
    validate_email_code_from_cache
from authentication.models import ForgetTypes
from common.constants import TwoFaCodesStorageTypes
from common.dependencies import get_db_session
from common.resources import response_strings
from common.resources.account_recovery import questions
from common.schemas import ResponseSchema
from db.pgsql.engine import AsyncDBSession
from files.shared.handlers import FolderStorage
from logger.loggers import APP_LOGGER
from logger.tasks import write_log
from rate_limiter import limiter
# This file handles all things related to forget 2fa or password
# forget email not needed, user will contact to support for that
from settings import settings

forget_router = APIRouter(
    prefix="/auth/forget",
    tags=["Forget routes"],
    dependencies=[])


@forget_router.get("/form")
async def get_forget_questions():
    """Returns current forget form questions"""
    return ResponseSchema(data=questions.questions)


@forget_router.post("/form")
@limiter.limit('3/day,9/month')
async def create_forget_request(request: Request, user: models.User = Depends(get_user_by_username),
                                answers: dict = Depends(get_answers_dict),
                                file: Optional[UploadFile] = File(None)):
    """create a record to the database for the user who lost his two factor code, to be
        checked by the admin later.
    """
    if user:
        answers_str = json.dumps(answers)
        file_id = None
        if file:
            file_id = await FolderStorage.save_file(file)
        async with AsyncDBSession() as async_session:
            await crud.create_forget_request(async_session, user,
                                             ForgetTypes.two_fa_forget, answers_str, file_id)

    return ResponseSchema(data={'msg': response_strings.FORGET_REQUEST_FORM_SUBMITTED})


@forget_router.post("/reset_password")
@limiter.limit('3/day,9/week')
async def reset_forgot_password(request: Request, bg_tasks: BackgroundTasks,
                                user: models.User = Depends(get_user_by_username),
                                tmp_token: str = Body(..., min_length=32, max_length=32),
                                email_code: str = Body(..., min_length=6, max_length=6),
                                two_fa_code: Optional[str] = Body(None, max_length=6),
                                new_hashed_password: str = Depends(hash_new_password),
                                async_session: AsyncSession = Depends(get_db_session)):
    """First check user exists or not, then verifies email code and finally checks
    if the user activated the 2fa auth, checks its 2fa code"""
    unauthorized_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=response_strings.WRONG_RESET_PASSWORD_INPUT)

    if not user:
        raise unauthorized_exception

    if not await validate_temp_token(user, tmp_token):
        raise unauthorized_exception

    if settings.TWO_FA_CODES_STORAGE == TwoFaCodesStorageTypes.DB:
        v_record = await get_email_verification_record_from_db(user, email_code)
        if v_record and \
                ((user.two_fa_enabled and verify_totp_code(user, two_fa_code)) or (not user.two_fa_enabled)):
            await crud.update_user(async_session, user, use_orm=False, hashed_password=new_hashed_password)
            bg_tasks.add_task(delete_unused_verification, v_record)
            bg_tasks.add_task(notify_password_changed, user)
            # Logout the user
            await delete_token(user)
            return ResponseSchema(data={"msg": response_strings.PASSWORD_CHANGED})
    elif settings.TWO_FA_CODES_STORAGE == TwoFaCodesStorageTypes.REDIS:
        if await validate_email_code_from_cache(user, email_code):
            await crud.update_user(async_session, user, use_orm=False, hashed_password=new_hashed_password)
            bg_tasks.add_task(notify_password_changed, user)
            # Logout the user
            await delete_token(user)
            return ResponseSchema(data={"msg": response_strings.PASSWORD_CHANGED})
    else:
        write_log(APP_LOGGER, 'warning', 'mail_verification_sender',
                  f"verification storage type {settings.TWO_FA_CODES_STORAGE} is not implemented.")
        raise NotImplementedError

    # TODO (Phase 2) don't allow to set old password
    raise unauthorized_exception
