from authentication.shared.classes import ThisUser
from authentication.shared.dependencies import get_this_user
from db.pgsql.engine import AsyncDBSession
from db.redis.handler import redis_get, redis_del_key
from db.redis.namespaces import notification_temp_token_namespace, notification_message_namespace
from notification import redis_actions, crud
from notification.schemas import Message
from notification.utils import get_id_key


async def check_client_token(token: str) -> ThisUser:
    username = await redis_get(notification_temp_token_namespace, token)
    if username is not None:
        user = await get_this_user(username)
        await redis_del_key(notification_temp_token_namespace, token)
        return user


async def send_notification(user: ThisUser, msg: Message, just_socket=False) -> int:
    """Publish message to notification channel"""
    queue_name = notification_message_namespace + ":" + get_id_key(user)
    if not just_socket:
        async with AsyncDBSession() as async_session:
            created_record = await crud.create_notification(async_session, user_id=user.id, data=msg.data)
            msg.id = created_record.id
    await redis_actions.push(queue_name, msg.dict())
    return msg.id


async def mark_as_read_by_socket_manager(notification_id: int):
    async with AsyncDBSession() as async_session:
        await crud.mark_as_read_notification(async_session, notification_id)


async def mark_as_read_by_user(notification_id: int, user_id: int):
    async with AsyncDBSession() as async_session:
        notification = await crud.get_notification(async_session, notification_id)
        if notification is not None and notification.user_id == user_id:
            if not notification.read:
                await crud.mark_as_read_notification(async_session, notification_id)
            return True
        else:
            return False


async def mark_all_as_read(user_id: int):
    async with AsyncDBSession() as async_session:
        await crud.mark_as_read_all_notification(async_session, user_id)
