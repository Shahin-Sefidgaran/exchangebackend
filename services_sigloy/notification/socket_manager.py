import asyncio
from typing import Dict

from starlette.websockets import WebSocket

from common.helpers import SingletonMeta
from db.redis.namespaces import notification_message_namespace
from notification import redis_actions
from notification.dependencies import mark_as_read_by_socket_manager


class SocketManager(metaclass=SingletonMeta):
    """Singleton class that handles all websocket notification connections in this worker"""

    def __init__(self):
        # id_ is the unique identifier of user (e.g. username)
        self._active_connections: Dict[str, WebSocket] = {}  # username: connection
        # Run message checker for ever without waiting for it
        asyncio.create_task(self.message_checker())

    async def connect(self, id_: str, websocket: WebSocket):
        if id_ in self._active_connections:
            await self.disconnect(id_)
        await websocket.accept()
        self._active_connections[id_] = websocket

    async def disconnect(self, id_: str):
        if id_ in self._active_connections:
            await self._active_connections[id_].close()
            self.remove_connection(id_)

    async def send_message(self, id_: str, message: str):
        await self._active_connections[id_].send_text(message)

    def remove_connection(self, id_: str):
        if id_ in self._active_connections:
            del self._active_connections[id_]

    async def broadcast(self, message: str):
        """Send message to all connections in this thread"""
        for id_, connection in self._active_connections.items():
            await connection.send_text(message)

    def is_online(self, id_):
        """This method can be used when we have just 1 worker, for more than 1 workers,
        this method can't be used because active_connections are not shared between threads."""
        return id_ in self._active_connections

    async def message_checker(self):
        """Checks the notification redis queue for each client for new messages"""
        while True:
            for id_, connection in self._active_connections.items():
                queue_name = notification_message_namespace + ":" + id_
                while True:
                    msg = await redis_actions.pop(queue_name)
                    if msg:
                        await connection.send_json(msg)
                        if msg['id'] is not None:
                            await mark_as_read_by_socket_manager(msg['id'])
                    else:
                        break
            else:
                await asyncio.sleep(0.1)
