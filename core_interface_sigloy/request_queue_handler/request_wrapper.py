from core.core_api import CoreApi
from db.pgsql.engine import AsyncDBSession
from db.redis.namespaces import request_queue_handler_namespace
from interface.crud import get_cex_keys
from interface.schemas import CoreRequestSchema
from logger.loggers import QUEUE_LOGGER
from logger.tasks import write_log
from request_queue_handler.redis_actions import put_result


class RequestWrapper:
    """Wrapping request to send it to the "Interface" and
        putting response to the redis again"""

    def __init__(self, req_id, data: dict):
        self.req_id = req_id
        self.data = CoreRequestSchema(**data)

    async def send(self):
        # Check if the user_id is set send
        write_log(QUEUE_LOGGER, 'info', 'request wrapper', 'received data' + str(self.data))
        if self.data.user_id:
            async with AsyncDBSession() as async_session:
                # TODO add caching here
                cex_keys = await get_cex_keys(async_session, self.data.user_id)
                core_api = CoreApi(cex_keys.access_id, cex_keys.secret_key)
        else:
            core_api = CoreApi()
        response = await core_api.http_request(self.data.target_func, **self.data.args)
        return await put_result(request_queue_handler_namespace, self.req_id, response.dict())
