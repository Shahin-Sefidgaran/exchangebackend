from typing import List, Optional

from fastapi import APIRouter, Path
from fastapi.background import BackgroundTasks
from fastapi.responses import ORJSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio.session import AsyncSession

from authentication.background_tasks import delete_unused_verification, new_login_happened, \
    notify_password_changed
from authentication.crud import get_a_free_cex_account, associate_cex_acc_to_user, get_cex_account, get_login_history
from authentication.dependencies.auth import *
from authentication.dependencies.auth import send_register_verification_mail
from authentication.dependencies.password import hash_new_password
from authentication.dependencies.token import create_and_save_access_token, delete_token
from authentication.dependencies.two_fa import send_2fa_code
from authentication.models import UserStatuses, VerificationTypes
from authentication.schemas import UserOut, LoginHistoryOut
from common.dependencies import get_db_session
from common.resources import response_strings
from common.schemas import ResponseSchema
from common.utils import get_offset_limit
from db.pgsql.engine import AsyncDBSession
from rate_limiter import limiter

auth_router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    dependencies=[])

templates = Jinja2Templates(directory='authentication/templates')


@auth_router.get("/login", name='login_page')
async def login_page():
    # TODO return react login page
    return 'Return react login page'


@auth_router.post("/login", name='')
@limiter.limit('8/hour,20/day')
async def login_for_temp_token(request: Request, bg_tasks: BackgroundTasks,
                               form_data: OAuth2PasswordRequestForm = Depends(),
                               async_session: AsyncDBSession = Depends(get_db_session)):
    """This route get username and password as input and return temp token
        for new requests in the future."""
    user = await authenticate_user(form_data.username, form_data.password, async_session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=response_strings.INCORRECT_LOGIN_CREDENTIALS,
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.status == UserStatuses.not_verified:
        return ResponseSchema(
            errors=[{'msg': response_strings.NOT_VERIFIED_EMAIL}])

    user_cex_acc = await get_cex_account(async_session, user)
    if user.status == UserStatuses.no_cex_acc or not user_cex_acc:
        return ResponseSchema(errors=[{'msg': response_strings.NO_CEX_ACCOUNT}])

    # sends api keys to the interface each time user logs in
    if await send_keys_to_if(user.id, user_cex_acc.access_id, user_cex_acc.secret_key):
        # disable 2fa for testing purposes
        if settings.ENABLE_TWO_FA:
            return await send_2fa_code(user)
        else:
            auth_data = await create_and_save_access_token(user)
            bg_tasks.add_task(new_login_happened, request, user)
            return ORJSONResponse(content=auth_data)
    else:
        return ResponseSchema(errors=[{'msg': response_strings.LOGIN_SERVER_PROBLEM}])
    # TODO (PHASE 2) Check device authorization and agent
    # TODO (PHASE 2) handles multiple devices if needed (in next phase of project)


@auth_router.get("/me", response_model=ResponseSchema)
async def user_info(current_user: models.User =
                    Depends(get_current_active_user)):
    """Returns user's information"""
    user_out = UserOut.from_orm(current_user)
    return ResponseSchema(data=user_out)


# slow route because of slow hash making function(bcrypt)
@auth_router.post("/register", status_code=201)
@limiter.limit('3/hour,10/day')
async def register_user(request: Request, created_user: models.User = Depends(create_user_or_fail)):
    """Registers new user"""
    # TODO (PHASE 2) add referral code
    await send_register_verification_mail(request, created_user)
    return ResponseSchema(data={'msg': response_strings.USER_CREATED_SUCCESSFULLY})


@auth_router.patch("/password")
async def change_password(bg_tasks: BackgroundTasks,
                          user: models.User = Depends(check_user_password),
                          new_hashed_password: str = Depends(hash_new_password),
                          async_session: AsyncSession = Depends(get_db_session)):
    """Changing user's password by using different dependencies"""
    await crud.update_user(async_session, user, use_orm=False, hashed_password=new_hashed_password)
    bg_tasks.add_task(notify_password_changed, user)
    return ResponseSchema(data={"msg": response_strings.PASSWORD_CHANGED})


@auth_router.get("/register/email/verify/{unique_id}")
@limiter.limit('5/hour,15/day')
async def verify_email(request: Request, unique_id: str, bg_tasks: BackgroundTasks):
    """Handles all email verification codes that has been sent by register route.
        First tries to get user by unique_id(path parameter), if id and user exists
        then tries to get a free cex account from the database to associate to the user
        and sets the user status to active, if couldn't set user status to "no_cex_acc".
        With a background task, verification record will be deleted after response.
    """
    async with AsyncDBSession() as async_session:
        # get user by unique string
        verification_record = await crud.get_verification_rec_by_code(async_session, unique_id,
                                                                      VerificationTypes.register_email_verify)
        if verification_record is None:
            return templates.TemplateResponse("email_verification_response.jinja2",
                                              context={'request': request,
                                                       'message': response_strings.WRONG_CODE_EMAIL_VERIFY,
                                                       'res': 'fail', 'redirect_url': '/'})

        user = verification_record.user
        # trying to get a free cex account
        cex_account = await get_a_free_cex_account(async_session)
        # Delete verification record in the background
        bg_tasks.add_task(delete_unused_verification, verification_record)
        # Checks is there free sex account or not
        if not cex_account:
            await crud.update_user(async_session, user, True, status=UserStatuses.no_cex_acc)
            return templates.TemplateResponse("email_verification_response.jinja2",
                                              context={'request': request,
                                                       'message': response_strings.NO_CEX_ACCOUNT,
                                                       'res': 'ok', 'redirect_url': '/'})
        else:
            await crud.update_user(async_session, user, True, status=UserStatuses.active)
            await associate_cex_acc_to_user(async_session, cex_account, user)
    login_url = request.url_for('login_page')
    return templates.TemplateResponse("email_verification_response.jinja2",
                                      context={'request': request,
                                               'message': response_strings.EMAIL_VERIFIED_SUCCESS,
                                               'res': 'ok', 'redirect_url': login_url})


@auth_router.get("/history/{page}", response_model=List[LoginHistoryOut])
async def history(page: Optional[int] = Path(0), current_user: models.User = Depends(get_current_active_user),
                  async_session=Depends(get_db_session)):
    """Get login history records"""
    offset, limit = get_offset_limit(page, 5)
    recent_logins = await get_login_history(async_session, current_user, offset=offset, limit=limit)
    return recent_logins


@auth_router.get("/logout")
async def logout(current_user: models.User =
                 Depends(get_current_active_user)):
    """Revokes user token from db"""
    # TODO (PHASE 2) just revoke current device token
    # TODO (PHASE 2) disconnect user from notifications socket
    await delete_token(current_user)
