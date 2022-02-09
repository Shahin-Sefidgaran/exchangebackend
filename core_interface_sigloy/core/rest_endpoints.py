import collections
import hashlib

import aiohttp

from common.utils import epoch_milliseconds
from logger.loggers import NETWORK_LOGGER
from logger.tasks import write_log
from .constants import HTTP_API_BASE_URL
from .exceptions import *


class CoreApi:
    _headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/60.0.3112.90 Safari/537.36 '
    }

    def __init__(self, access_id=None, secret_key=None):
        self._access_id = access_id
        self._secret_key = secret_key

    # Version 1 core api request schema
    async def _v1(self, path, method='get', auth=False, **params):
        # TODO handle exceptions during sending request
        access_id = self._access_id
        secret_key = self._secret_key

        url = HTTP_API_BASE_URL + 'v1/' + path
        headers = dict(self._headers)
        if auth:
            if not access_id or not secret_key:
                raise ApiKeyNotSetError('API keys not configured')

            params.update(access_id=access_id)
            params.update(tonce=epoch_milliseconds())

        params = collections.OrderedDict(sorted(params.items()))

        if auth:
            headers.update(Authorization=self._sign(params, secret_key))

        async with aiohttp.ClientSession() as session:
            if method == 'post':
                async with session.post(url, json=params, headers=headers) as resp:
                    return self._process_response(await resp.json())
            else:
                async with session.request(method=method, url=url, params=params, headers=headers) as resp:
                    return self._process_response(await resp.json())

    @staticmethod
    def _process_response(data):
        # TODO CHECK LATER
        if data['code'] != 0:
            raise ResponseCodeError(data['message'])
        return data['data']

    @staticmethod
    def _sign(params, secret_key):
        data = '&'.join([key + '=' + str(params[key])
                         for key in sorted(params)])
        data = data + '&secret_key=' + secret_key
        data = data.encode()
        return hashlib.md5(data).hexdigest().upper()


class MarketApi(CoreApi):
    async def market_list(self):
        return await self._v1('market/list')

    async def market_ticker(self, market):
        return await self._v1('market/ticker', market=market)

    async def market_ticker_all(self):
        return await self._v1('market/ticker/all')

    async def market_depth(self, market, merge='0.00000001', **params):
        return await self._v1('market/depth', market=market, merge=merge, **params)

    async def market_deals(self, market, **params):
        return await self._v1('market/deals', market=market, **params)

    async def market_kline(self, market, type='1hour', **params):
        return await self._v1('market/kline', market=market, type=type, **params)

    async def market_info(self):
        return await self._v1('market/info')

    async def market_detail(self, market):
        return await self._v1('market/detail', market=market)

    async def amm_market(self, market):
        return await self._v1('amm/market', market=market)


class OrderApi(CoreApi):
    async def order_limit(self, market, type, amount, price, **params):
        return await self._v1('order/limit', method='post', auth=True, market=market, type=type, amount=amount,
                              price=price,
                              **params)
    
    async def order_stop_limit(self, market, type, amount, price,stop_price, **params):
        return await self._v1('order/stop/limit', method='post', auth=True, market=market, type=type, amount=amount,
                              price=price,stop_price=stop_price,
                              **params)

    async def order_limit_batch(self, market, type, amount, price, batch_orders, **params):
        return await self._v1('order/limit/batch', method='post', auth=True, market=market, type=type, amount=amount,
                              price=price, batch_orders=batch_orders, **params)

    async def order_market(self, market, type, amount, **params):
        return await self._v1('order/market', method='post', auth=True, market=market, type=type, amount=amount,
                              **params)

    async def order_ioc(self, market, type, amount, price, **params):
        return await self._v1('order/ioc', method='post', auth=True, market=market, type=type, amount=amount,
                              price=price,
                              **params)

    async def order_pending(self, page=1, limit=100, **params):
        return await self._v1('order/pending', method='get', auth=True, page=page, limit=limit, **params)

    async def order_finished(self, page=1, limit=100, **params):
        return await self._v1('order/finished', method='get', auth=True, page=page, limit=limit, **params)

    async def order_status(self, market, id):
        return await self._v1('order/status', method='get', auth=True, market=market, id=id)

    async def order_status_batch(self, market, batch_ids):
        return await self._v1('order/status/batch', method='get', auth=True, market=market, batch_ids=batch_ids)

    async def order_deals(self, id, page=1, limit=100):
        return await self._v1('order/deals', method='get', auth=True, id=id, page=page, limit=limit)

    async def order_user_deals(self, market, page=1, limit=100):
        return await self._v1('order/user/deals', method='get', auth=True, market=market, page=page, limit=limit)

    async def order_pending_cancel(self, market, id):
        return await self._v1('order/pending', method='delete', auth=True, market=market, id=id)

    async def order_pending_cancel_batch(self, market, batch_ids):
        return await self._v1('order/pending/batch', method='delete', auth=True, market=market, batch_ids=batch_ids)

    async def order_pending_cancel_all(self, account_id, market):
        return await self._v1('order/pending', method='delete', auth=True, account_id=account_id, market=market)

    async def order_mining_difficulty(self):
        return await self._v1('order/mining/difficulty', method='get', auth=True)


class AccountApi(CoreApi):
    async def credit_account_info(self):
        return await self._v1('credit/info', auth=True)

    async def balance_info(self):
        return await self._v1('balance/info', auth=True)

    async def balance_coin_withdraw_list(self, **params):
        return await self._v1('balance/coin/withdraw', auth=True, **params)

    async def balance_coin_withdraw(self, coin_type, coin_address, actual_amount, transfer_method, **params):
        return await self._v1('balance/coin/withdraw', method='post', auth=True, coin_type=coin_type,
                              coin_address=coin_address, actual_amount=actual_amount, transfer_method=transfer_method,
                              **params)

    async def balance_coin_withdraw_cancel(self, coin_withdraw_id, **params):
        return await self._v1('balance/coin/withdraw', method='delete', auth=True, coin_withdraw_id=coin_withdraw_id,
                              **params)

    async def balance_coin_deposit_list(self, **params):
        return await self._v1('balance/coin/deposit', auth=True, **params)

    async def balance_deposit_address(self, coin_type, **params):
        return await self._v1('balance/deposit/address/{}'.format(coin_type), auth=True, **params)

    async def balance_deposit_address_new(self, coin_type, **params):
        return await self._v1('balance/deposit/address/{}'.format(coin_type), method='post', auth=True, **params)

    async def sub_account_transfer(self, coin_type, amount, **params):
        return await self._v1('sub_account/transfer', method='post', auth=True, coin_type=coin_type, amount=amount,
                              **params)

    async def sub_account_balance(self, **params):
        return await self._v1('sub_account/balance', auth=True, **params)

    async def sub_account_transfer_history(self, **params):
        return await self._v1('sub_account/balance', auth=True, **params)


class MarginApi(CoreApi):
    async def margin_transfer(self, from_account, to_account, coin_type, amount):
        return await self._v1('margin/transfer', method='post', auth=True, from_account=from_account,
                              to_account=to_account,
                              coin_type=coin_type, amount=amount)

    async def margin_account(self, **params):
        return await self._v1('margin/account', auth=True, **params)

    async def margin_account_currency(self, market):
        return await self._v1('margin/account', auth=True, market=market)

    async def margin_config(self, **params):
        return await self._v1('margin/config', auth=True, **params)

    async def margin_config_currency(self, market):
        return await self._v1('margin/config', auth=True, market=market)

    async def margin_loan_history(self, **params):
        return await self._v1('margin/loan/history', auth=True, **params)

    async def margin_loan(self, market, coin_type, amount):
        return await self._v1('margin/loan', method='post', auth=True, market=market, coin_type=coin_type,
                              amount=amount)

    async def margin_flat(self, market, coin_type, amount, **params):
        return await self._v1('margin/flat', method='post', auth=True, market=market, coin_type=coin_type,
                              amount=amount,
                              **params)


class CommonApi(CoreApi):
    async def currency_rate(self):
        return await self._v1('common/currency/rate')

    async def asset_config(self, **params):
        return await self._v1('common/asset/config', **params)


class ContractApi(CoreApi):
    # perpetual balance transfer
    async def contract_balance_transfer(self, coin_type, amount, transfer_side):
        return await self._v1('contract/balance/transfer', method='post', auth=True, coin_type=coin_type, amount=amount,
                              transfer_side=transfer_side)


class PerpetualApi(CoreApi):
    """
    because of different sign function and parameters and url we have
    been overwritten these functions.
    "p" at the beginning of every thing's name stands for "perpetual".
    """

    # Version 1 perpetual api
    async def _p_v1(self, path, method='get', auth=False, **params):
        # TODO handle exceptions during sending request
        # TODO handle slowdown exception
        access_id = self._access_id
        secret_key = self._secret_key

        # api structure is different with parent class
        url = HTTP_API_BASE_URL + 'perpetual/' + 'v1/' + path
        headers = dict(self._headers)
        if auth:
            if not access_id or not secret_key:
                raise ApiKeyNotSetError('API keys not configured')
            # here are differences with parent _v1 method
            headers['AccessId'] = access_id
            params.update(timestamp=epoch_milliseconds())

        params = collections.OrderedDict(sorted(params.items()))
        if auth:
            headers.update(Authorization=self._p_sign(params, secret_key))

        async with aiohttp.ClientSession() as session:
            if method == 'post':
                async with session.post(url, data=params, headers=headers) as resp:
                    return self._process_response(await resp.json())
            else:
                async with session.request(method=method, url=url, params=params, headers=headers) as resp:
                    write_log(NETWORK_LOGGER, 'debug', 'core', f'received response:{await resp.text()}')
                    return self._process_response(await resp.json())

    @staticmethod
    def _p_sign(params, secret_key):
        data = ['='.join([str(k), str(v)]) for k, v in params.items()]
        str_params = "{0}&secret_key={1}".format(
            '&'.join(data), secret_key).encode()
        token = hashlib.sha256(str_params).hexdigest()
        return token

    async def ping(self):
        return await self._p_v1('ping', method='get')

    async def time(self):
        return await self._p_v1('time', method='get')

    async def p_market_list(self):
        return await self._p_v1('market/list', method='get')

    async def market_limit_config(self):
        return await self._p_v1('market/limit_config', method='get')

    async def p_market_ticker(self, market):
        return await self._p_v1('market/ticker', method='get', market=market)

    async def p_market_depth(self, market, merge, limit):
        return await self._p_v1('market/depth', method='get', market=market, merge=merge, limit=limit)

    async def p_market_deals(self, market, **params):
        return await self._p_v1('market/deals', method='get', market=market, **params)

    async def market_funding_history(self, market, offset, limit, **params):
        return await self._p_v1('market/funding_history', method='get', market=market, offset=offset, limit=limit,
                                **params)

    async def market_user_deals(self, market, side, offset, limit, **params):
        return await self._p_v1('market/user_deals', method='get', market=market, side=side, offset=offset, limit=limit,
                                **params)

    async def p_market_kline(self, market, type, **params):
        return await self._p_v1('market/kline', method='get', market=market, type=type, **params)

    async def adjust_leverage(self, market, leverage, position_type, **params):
        """
        Args:
            position_type (Int): 1 Isolated - 2 Cross
        """
        return await self._p_v1('market/adjust_leverage', method='post', auth=True, market=market,
                                position_type=position_type,
                                leverage=leverage, **params)

    async def get_position_amount(self, market, price, side, **params):
        return await self._p_v1('market/position_expect', method='post', auth=True, market=market, price=price,
                                side=side,
                                **params)

    async def asset_query(self):
        return await self._p_v1('asset/query', method='get', auth=True)

    async def put_limit_order(self, market, amount, price, side, **params):
        return await self._p_v1('order/put_limit', method='post', auth=True, market=market, amount=amount, price=price,
                                side=side, **params)

    async def put_market_order(self, market, side, amount, **params):
        return await self._p_v1('order/put_market', method='post', auth=True, market=market, side=side, amount=amount,
                                **params)

    async def put_stop_limit_order(self, market, amount, side, price, stop_type, stop_price, **params):
        return await self._p_v1('order/put_stop_limit', method='post', auth=True, market=market, amount=amount,
                                side=side,
                                price=price, stop_type=stop_type, stop_price=stop_price, **params)

    async def put_stop_market_order(self, market, amount, side, stop_type, stop_price, **params):
        return await self._p_v1('order/put_stop_market', method='post', auth=True, market=market, amount=amount,
                                side=side,
                                stop_type=stop_type, stop_price=stop_price, **params)

    async def put_limit_close_order(self, market, position_id, amount, price, **params):
        return await self._p_v1('order/close_limit', method='post', auth=True, market=market, position_id=position_id,
                                amount=amount, price=price, **params)

    async def put_market_close_order(self, market, position_id, **params):
        return await self._p_v1('order/close_market', method='post', auth=True, market=market, position_id=position_id,
                                **params)

    async def cancel_pending_order(self, market, order_id, **params):
        return await self._p_v1('order/cancel', method='post', auth=True, market=market, order_id=order_id, **params)

    async def cancel_pending_order_all(self, market, **params):
        return await self._p_v1('order/cancel_all', method='post', auth=True, market=market, **params)

    async def cancel_pending_stop_order(self, market, order_id, **params):
        return await self._p_v1('order/cancel_stop', method='post', auth=True, market=market, order_id=order_id,
                                **params)

    async def query_pending_order(self, market, side, offset, limit, **params):
        return await self._p_v1('order/pending', method='get', auth=True, market=market, side=side, offset=offset,
                                limit=limit,
                                **params)

    async def query_finished_order(self, market, side, offset, limit, **params):
        return await self._p_v1('order/finished', method='get', auth=True, market=market, side=side, offset=offset,
                                limit=limit,
                                **params)

    async def query_stop_order(self, market, side, offset, limit, **params):
        return await self._p_v1('order/stop_pending', method='get', auth=True, market=market, side=side, offset=offset,
                                limit=limit, **params)

    async def query_order_status(self, market, order_id, **params):
        return await self._p_v1('order/status', method='get', auth=True, market=market, order_id=order_id, **params)

    async def query_pending_position(self, **params):
        return await self._p_v1('position/pending', method='get', auth=True, **params)

    async def adjust_position_margin(self, market, amount, type, **params):
        return await self._p_v1('position/adjust_margin', method='post', auth=True, market=market, amount=amount,
                                type=type,
                                **params)
