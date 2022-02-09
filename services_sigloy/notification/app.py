from typing import List, Optional

from fastapi import WebSocket, APIRouter, Depends, HTTPException, Path
from starlette import status
from starlette.websockets import WebSocketDisconnect

from authentication.shared.classes import ThisUser
from authentication.shared.dependencies import this_user
from common.dependencies import get_db_session
from common.resources import response_strings
from common.schemas import ResponseSchema
from common.utils import unique_string_gen, get_offset_limit
from db.redis.handler import redis_save
from db.redis.namespaces import notification_temp_token_namespace
from notification import crud
from notification.dependencies import check_client_token, send_notification, mark_as_read_by_user, mark_all_as_read
from notification.schemas import Message, NotificationOut
from notification.socket_manager import SocketManager
from notification.utils import get_id_key
from settings import settings

notification_router = APIRouter(
    prefix='/notification',
    tags=["Notification"],
    dependencies=[])


@notification_router.get("/token")
async def get_token(user: ThisUser = Depends(this_user)):
    temp_token = unique_string_gen()
    await redis_save(notification_temp_token_namespace, temp_token, user.username, settings.NOTIFICATION_TOKEN_TIMEOUT)
    return ResponseSchema(data={'temp_token': temp_token})


# This route doesn't have "/notify" prefix
@notification_router.websocket("/{token}/ws")
async def websocket_endpoint(token: str, websocket: WebSocket):
    socket_manager = SocketManager()
    user = await check_client_token(token)
    if not user:
        await websocket.close()
        return

    id_ = get_id_key(user)
    await socket_manager.connect(id_, websocket)
    try:
        while True:
            # we might need later to receive some data in this socket
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        socket_manager.remove_connection(id_)


if settings.DEBUG:
    # This is a test route
    @notification_router.get("/notify")
    async def notify_user(user: ThisUser = Depends(this_user)):
        notification_id = await send_notification(user, Message(data='This is my message'))
        return ResponseSchema(data={'msg': 'done', 'notification_id': notification_id})


@notification_router.get("/news/{page}", response_model=List[NotificationOut])
async def get_new_notifications(page: Optional[int] = Path(0), user: ThisUser = Depends(this_user),
                                async_session=Depends(get_db_session)):
    """Returns paginated new notifications"""
    offset, limit = get_offset_limit(page, 5)
    return await crud.get_new_notifications(async_session, user, offset=offset, limit=limit)


@notification_router.get("/read/{notif_id}")
async def read_notifications(notif_id: int, user: ThisUser = Depends(this_user)):
    if await mark_as_read_by_user(notif_id, user.id):
        return ResponseSchema(data={'msg': 'done'})
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=response_strings.INVALID_NOTIFICATION_TO_READ)


@notification_router.get("/read_all")
async def read_all_notifications(user: ThisUser = Depends(this_user)):
    await mark_all_as_read(user.id)
    return ResponseSchema(data={'msg': 'done'})
