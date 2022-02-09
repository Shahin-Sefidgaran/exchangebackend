from authentication.shared.classes import ThisUser
from notification.dependencies import send_notification
from notification.schemas import Message
from notification.socket_manager import SocketManager
from notification.utils import get_id_key


def initiate_notification_socket_manager():
    _ = SocketManager()


class NotificationMessage(Message):
    pass


async def notify(user: ThisUser, msg: Message, just_socket=False):
    return await send_notification(user, msg, just_socket)


async def disconnect_user(user: ThisUser) -> None:
    """Disconnect user from notification channel"""
    socket_manager = SocketManager()
    await socket_manager.disconnect(get_id_key(user))
