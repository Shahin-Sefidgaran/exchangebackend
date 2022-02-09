from common.schemas import ResponseSchema
from logger.loggers import NETWORK_LOGGER
from logger.tasks import write_log
from .exceptions import ResponseCodeError
from .rest_endpoints import CommonApi, MarginApi, MarketApi, OrderApi, AccountApi, ContractApi, PerpetualApi


class CoreApi(CommonApi, MarginApi, MarketApi, OrderApi, AccountApi, ContractApi, PerpetualApi):
    """This class includes async functions of core endpoint apis"""

    async def http_request(self, operation, **arguments):
        """Always use this method to send requests to the core, this will
        handle exceptions"""

        method = self.get_instance_operation(operation)
        if method is None:
            return ResponseSchema(status='fail', errors=[{'msg': 'method not found'}])
        try:
            write_log(NETWORK_LOGGER, 'debug', 'core interface', f'sending request to {operation} route')
            write_log(NETWORK_LOGGER, 'debug', 'core interface', f'request arguments: {arguments}')
            response = await method(**arguments)
            write_log(NETWORK_LOGGER, 'debug', 'core interface', f'response: {response}')
        except ResponseCodeError as e:
            return ResponseSchema(status='fail', errors=[{'msg': e.args[0]}])
        # TODO handle other exceptions during network
        else:
            return ResponseSchema(data=response)

    def get_instance_operation(self, op: str):
        # need to pass last "None" parameter to prevent throwing exceptions
        return getattr(self, op, None)

    @staticmethod
    def get_class_operation(op: str):
        # need to pass last "None" parameter to prevent throwing exceptions
        return getattr(CoreApi, op, None)

    def ws_request(self):
        pass
