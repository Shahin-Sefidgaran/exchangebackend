import pyotp
from fastapi import APIRouter, HTTPException, Depends
from fastapi import status
from fastapi.background import BackgroundTasks
from fastapi.responses import ORJSONResponse
from starlette.requests import Request

from authentication import models, crud
from authentication.background_tasks import delete_unused_verification
from authentication.dependencies.auth import get_user, get_current_active_user, get_user_by_username
from authentication.dependencies.token import validate_temp_token
from authentication.dependencies.two_fa import create_access_token, get_email_verification_record_from_db, verify_totp_code, verify_totp_dep, \
    validate_email_code_from_cache, send_2fa_code
from authentication.schemas import Get2FA, Verify2FA
from common.constants import TwoFaCodesStorageTypes
from common.resources import response_strings
from common.schemas import ResponseSchema
from common.utils import unique_string_gen
from db.pgsql.engine import AsyncDBSession
from logger.loggers import APP_LOGGER
from logger.tasks import write_log
from rate_limiter import limiter
from settings import settings

two_fa_router = APIRouter(
    prefix="/auth/2fa",
    tags=["Two Factor Authentication"],
    dependencies=[])


@two_fa_router.get('/activate')
@limiter.limit('5/hour,10/day')
async def pre_activate(request: Request,
                       current_user: models.User = Depends(get_current_active_user)):
    """Create a new secret key by using TOTP algorithm for the user and
    save it to the DB, but not activate it until user send the code in
    activate 2fa route"""
    if current_user.two_fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=response_strings.TWO_FA_IS_ACTIVATE)
    # create a new secret key
    secret = pyotp.random_base32()
    # generate g-auth uri to show to the user
    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=current_user.username,
                                                   issuer_name=settings.APP_NAME)
    # saves to the db
    async with AsyncDBSession() as async_session:
        await crud.update_user(async_session, user=current_user, use_orm=False,
                               two_fa_secret_key=secret)
    return ResponseSchema(data={'uri': uri})


@two_fa_router.post('/activate')
async def activate_2fa(current_user: models.User = Depends(verify_totp_dep)):
    """Activate user 2fa by validating the code"""
    async with AsyncDBSession() as async_session:
        await crud.update_user(async_session, user=current_user, use_orm=False,
                               two_fa_enabled=True)
    return ResponseSchema(data={'msg': response_strings.TWO_FA_ACTIVATED})


@two_fa_router.post('/deactivate')
async def deactivate_2fa(current_user: models.User = Depends(verify_totp_dep)):
    """Set user 2fa to false if it's enable else raise exception"""
    if not current_user.two_fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=response_strings.TWO_FA_IS_DEACTIVATE)
    async with AsyncDBSession() as async_session:
        await crud.update_user(async_session, user=current_user, use_orm=False,
                               two_fa_enabled=False)
    return ResponseSchema(data={'msg': response_strings.TWO_FA_DEACTIVATED})


@two_fa_router.post('/verify')
@limiter.limit('10/hour,30/day')
async def verify_2fa(request: Request, verify_inputs: Verify2FA, bg_tasks: BackgroundTasks):
    """This route first checks email 2fa code and then checks if other 2 fa (g auth)
        is enabled, verifies that code. Parameter two_fa_code is optional, but should be
        provided when user is activated 2fa.
    """
    authentication_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=response_strings.WRONG_2FA_INPUTS)
    wrong_2fa_code = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=response_strings.WRONG_2FA_CODE)

    async with AsyncDBSession() as async_session:
        user = await get_user(verify_inputs.username, async_session)
        if not user:
            raise authentication_exception
        # checks temp token
        if not await validate_temp_token(user, verify_inputs.tmp_token):
            raise authentication_exception
        
        # check 2fa code
        if user.two_fa_enabled:
            # two_fa_code is not present
            if not verify_totp_code(user, verify_inputs.two_fa_code):
                raise wrong_2fa_code

            return ORJSONResponse(content= await create_access_token(request, user, bg_tasks))

        # checks email verification code
        if settings.TWO_FA_CODES_STORAGE == TwoFaCodesStorageTypes.DB:
            v_record = await get_email_verification_record_from_db(user, verify_inputs.email_code)
            if not v_record:
                raise wrong_2fa_code
            else:
                bg_tasks.add_task(delete_unused_verification, v_record)
        elif settings.TWO_FA_CODES_STORAGE == TwoFaCodesStorageTypes.REDIS:
            if not await validate_email_code_from_cache(user, verify_inputs.email_code):
                raise wrong_2fa_code
        else:
            write_log(APP_LOGGER, 'warning', 'mail_verification_sender',
                      f"verification storage type {settings.TWO_FA_CODES_STORAGE} is not implemented.")
            raise NotImplementedError

        return ORJSONResponse(content= await create_access_token(request, user, bg_tasks))


@two_fa_router.post("/get_email_code")
# @limiter.limit('5/hour,20/day')
async def get_email_code(request: Request, user: models.User = Depends(get_user_by_username)):
    """Send 2fa codes (mail, 2fa, mobile, etc), first checks which of them is enabled
    then sends them to get verified later."""
    if user:
        return await send_2fa_code(user)

    # returns a fake answer if the username is invalid to prevent username brute force attack
    fake_response = ResponseSchema(data={'msg': response_strings.TWO_FA_CODE_SENT,
                                         'tmp_token': unique_string_gen(),
                                         'types': ['email']})
    return fake_response


@two_fa_router.get("/status_2fa")
async def check_2fa(user: models.User = Depends(get_current_active_user)):
    return ResponseSchema(data={'two_fa_enabled': user.two_fa_enabled})


@two_fa_router.post("/check_2fa_code")
async def check_2fa_code(verify_inputs: Get2FA, user: models.User = Depends(get_current_active_user)):
    if user.two_fa_enabled:
        # two_fa_code is not present9
        if not verify_totp_code(user, verify_inputs.two_fa_code):
            return ResponseSchema(status="fail", errors=[{'msg': response_strings.WRONG_2FA_CODE}])

        return ResponseSchema(data={'msg': response_strings.TWO_FA_IS_CORRECT})

    return ResponseSchema(status="fail", errors=[{'msg': response_strings.TWO_FA_DEACTIVATED}])
