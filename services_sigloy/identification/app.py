import datetime
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, Depends

from authentication.shared.classes import ThisUser
from authentication.shared.dependencies import this_user
from common.dependencies import get_db_session
from common.resources import response_strings, notification_strings
from common.schemas import ResponseSchema
from common.utils import filter_dict, email_censor
from db.pgsql.engine import AsyncDBSession
from files.shared.handlers import FolderStorage
from identification import crud
from identification.schemas import UserInfoOut
from notification.shared import notify, NotificationMessage

profile_router = APIRouter(
    prefix="/profile",
    tags=["Profile"],
    dependencies=[])


@profile_router.put('/info')
async def update_info(first_name: Optional[str] = Form(None),
                      last_name: Optional[str] = Form(None),
                      birth_day: Optional[datetime.date] = Form(None),
                      country: Optional[str] = Form(None),
                      region: Optional[str] = Form(None),
                      city: Optional[str] = Form(None),
                      postal_code: Optional[str] = Form(None),
                      telephone: Optional[str] = Form(None),
                      national_id: Optional[str] = Form(None),
                      passport_number: Optional[str] = Form(None),
                      verify_image: UploadFile = File(None),
                      id_image: UploadFile = File(None),
                      passport_image: UploadFile = File(None),
                      user: ThisUser = Depends(this_user)):
    if verify_image:
        verify_image = await FolderStorage.save_file(verify_image)
    if id_image:
        id_image = await FolderStorage.save_file(id_image)
    if passport_image:
        passport_image = await FolderStorage.save_file(passport_image)

    user_id = user.id
    # locals() get all local variables instead of writing all of them by hand
    arguments = filter_dict({"user"}, locals(), exclude=True)  # remove user from arguments dict

    async with AsyncDBSession() as async_session:
        user_info = await crud.get_user_info(async_session=async_session, user_id=user_id)
        if user_info:
            await crud.update_user_info(async_session, user_info, use_orm=True, **arguments)
        else:
            user_info = await crud.create_user_info(async_session, **arguments)
    await notify(user, NotificationMessage(data=notification_strings.PROFILE_UPDATED))
    return ResponseSchema(data={'msg': response_strings.USER_INFO_UPDATED})


@profile_router.get('/info')
async def get_info(user: ThisUser = Depends(this_user), async_session=Depends(get_db_session)):
    user_info = await crud.get_user_info(async_session, user_id=user.id)
    if not user_info:
        user_info = await crud.create_user_info(async_session, user_id=user.id)
    data = UserInfoOut.from_orm(user_info)
    data.email = email_censor(user.email)
    
    return ResponseSchema(data=data)
