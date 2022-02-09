import collections
import hashlib

import aiohttp

from common.utils import epoch_milliseconds
from core.auth import ApiKeys
from .constants import HTTP_API_BASE_URL
from .exceptions import *


class CoreApi:
    _headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/60.0.3112.90 Safari/537.36 '
    }

    # Version 1 core api request schema
    @staticmethod
    async def _v1(path, method='get', auth=False, **params):
        # TODO handle exceptions during sending request
        access_id, secret_key = ApiKeys.get_keys()

        url = HTTP_API_BASE_URL + 'v1/' + path
        headers = dict(CoreApi._headers)
        if auth:
            if not access_id or not secret_key:
                raise ApiKeyNotSetError('API keys not configured')

            params.update(access_id=access_id)
            params.update(tonce=epoch_milliseconds())

        params = collections.OrderedDict(sorted(params.items()))

        if auth:
            headers.update(Authorization=CoreApi._sign(params, secret_key))

        async with aiohttp.ClientSession() as session:
            if method == 'post':
                async with session.post(url, json=params, headers=headers) as resp:
                    return CoreApi._process_response(await resp.json())
            else:
                async with session.request(method=method, url=url, params=params, headers=headers) as resp:
                    return CoreApi._process_response(await resp.json())

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
    @classmethod
    async def market_list(cls):
        return await cls._v1('market/list')

    @classmethod
    async def market_ticker(cls, market):
        return await cls._v1('market/ticker', market=market)

    @classmethod
    async def market_ticker_all(cls):
        return await cls._v1('market/ticker/all')

    @classmethod
    async def market_depth(cls, market, merge='0.00000001', **params):
        return await cls._v1('market/depth', market=market, merge=merge, **params)

    @classmethod
    async def market_deals(cls, market, **params):
        return await cls._v1('market/deals', market=market, **params)

    @classmethod
    async def market_kline(cls, market, type='1hour', **params):
        return await cls._v1('market/kline', market=market, type=type, **params)

    @classmethod
    async def market_info(cls):
        return await cls._v1('market/info')

    @classmethod
    async def market_detail(cls, market):
        return await cls._v1('market/detail', market=market)

    @classmethod
    async def amm_market(cls, market):
        return await cls._v1('amm/market', market=market)


class OrderApi(CoreApi):
    @classmethod
    async def order_limit(cls, market, type, amount, price, **params):
        return await cls._v1('order/limit', method='post', auth=True, market=market, type=type, amount=amount,
                             price=price,
                             **params)

    @classmethod
    async def order_limit_batch(cls, market, type, amount, price, batch_orders, **params):
        return await cls._v1('order/limit/batch', method='post', auth=True, market=market, type=type, amount=amount,
                             price=price, batch_orders=batch_orders, **params)

    @classmethod
    async def order_market(cls, market, type, amount, **params):
        return await cls._v1('order/market', method='post', auth=True, market=market, type=type, amount=amount,
                             **params)

    @classmethod
    async def order_ioc(cls, market, type, amount, price, **params):
        return await cls._v1('order/ioc', method='post', auth=True, market=market, type=type, amount=amount,
                             price=price,
                             **params)

    @classmethod
    async def order_pending(cls, market, page=1, limit=100):
        return await cls._v1('order/pending', method='get', auth=True, market=market, page=page, limit=limit)

    @classmethod
    async def order_finished(cls, market, page=1, limit=100):
        return await cls._v1('order/finished', method='get', auth=True, market=market, page=page, limit=limit)

    @classmethod
    async def order_status(cls, market, id):
        return await cls._v1('order/status', method='get', auth=True, market=market, id=id)

    @classmethod
    async def order_status_batch(cls, market, batch_ids):
        return await cls._v1('order/status/batch', method='get', auth=True, market=market, batch_ids=batch_ids)

    @classmethod
    async def order_deals(cls, id, page=1, limit=100):
        return await cls._v1('order/deals', method='get', auth=True, id=id, page=page, limit=limit)

    @classmethod
    async def order_user_deals(cls, market, page=1, limit=100):
        return await cls._v1('order/user/deals', method='get', auth=True, market=market, page=page, limit=limit)

    @classmethod
    async def order_pending_cancel(cls, market, id):
        return await cls._v1('order/pending', method='delete', auth=True, market=market, id=id)

    @classmethod
    async def order_pending_cancel_batch(cls, market, batch_ids):
        return await cls._v1('order/pending/batch', method='delete', auth=True, market=market, batch_ids=batch_ids)

    @classmethod
    async def order_pending_cancel_all(cls, account_id, market):
        return await cls._v1('order/pending', method='delete', auth=True, account_id=account_id, market=market)

    @classmethod
    async def order_mining_difficulty(cls):
        return await cls._v1('order/mining/difficulty', method='get', auth=True)


class AccountApi(CoreApi):
    @classmethod
    async def credit_account_info(cls):
        return await cls._v1('credit/info', auth=True)

    @classmethod
    async def balance_info(cls):
        return await cls._v1('balance/info', auth=True)

    @classmethod
    async def balance_coin_withdraw_list(cls, **params):
        return await cls._v1('balance/coin/withdraw', auth=True, **params)

    @classmethod
    async def balance_coin_withdraw(cls, coin_type, coin_address, actual_amount, transfer_method, **params):
        return await cls._v1('balance/coin/withdraw', method='post', auth=True, coin_type=coin_type,
                             coin_address=coin_address, actual_amount=actual_amount, transfer_method=transfer_method,
                             **params)

    @classmethod
    async def balance_coin_withdraw_cancel(cls, coin_withdraw_id, **params):
        return await cls._v1('balance/coin/withdraw', method='delete', auth=True, coin_withdraw_id=coin_withdraw_id,
                             **params)

    @classmethod
    async def balance_coin_deposit_list(cls, **params):
        return await cls._v1('balance/coin/deposit', auth=True, **params)

    @classmethod
    async def balance_deposit_address(cls, coin_type, **params):
        return await cls._v1('balance/deposit/address/{}'.format(coin_type), auth=True, **params)

    @classmethod
    async def balance_deposit_address_new(cls, coin_type, **params):
        return await cls._v1('balance/deposit/address/{}'.format(coin_type), method='post', auth=True, **params)

    @classmethod
    async def sub_account_transfer(cls, coin_type, amount, **params):
        return await cls._v1('sub_account/transfer', method='post', auth=True, coin_type=coin_type, amount=amount,
                             **params)

    @classmethod
    async def sub_account_balance(cls, **params):
        return await cls._v1('sub_account/balance', auth=True, **params)

    @classmethod
    async def sub_account_transfer_history(cls, **params):
        return await cls._v1('sub_account/balance', auth=True, **params)


class MarginApi(CoreApi):
    @classmethod
    async def margin_transfer(cls, from_account, to_account, coin_type, amount):
        return await cls._v1('margin/transfer', method='post', auth=True, from_account=from_account,
                             to_account=to_account,
                             coin_type=coin_type, amount=amount)

    @classmethod
    async def margin_account(cls, **params):
        return await cls._v1('margin/account', auth=True, **params)

    @classmethod
    async def margin_account_currency(cls, market):
        return await cls._v1('margin/account', auth=True, market=market)

    @classmethod
    async def margin_config(cls, **params):
        return await cls._v1('margin/config', auth=True, **params)

    @classmethod
    async def margin_config_currency(cls, market):
        return await cls._v1('margin/config', auth=True, market=market)

    @classmethod
    async def margin_loan_history(cls, **params):
        return await cls._v1('margin/loan/history', auth=True, **params)

    @classmethod
    async def margin_loan(cls, market, coin_type, amount):
        return await cls._v1('margin/loan', method='post', auth=True, market=market, coin_type=coin_type, amount=amount)

    @classmethod
    async def margin_flat(cls, market, coin_type, amount, **params):
        return await cls._v1('margin/flat', method='post', auth=True, market=market, coin_type=coin_type, amount=amount,
                             **params)


class CommonApi(CoreApi):
    @classmethod
    async def currency_rate(cls):
        return await cls._v1('common/currency/rate')

    @classmethod
    async def asset_config(cls, **params):
        return await cls._v1('common/asset/config', **params)


class ContractApi(CoreApi):
    # perpetual balance transfer
    @classmethod
    async def contract_balance_transfer(cls, coin_type, amount, transfer_side):
        return await cls._v1('contract/balance/transfer', method='post', auth=True, coin_type=coin_type, amount=amount,
                             transfer_side=transfer_side)


class PerpetualApi(CoreApi):
    # "p" at the beginning of function name stands for perpetual
    # Version 1 perpetual api
    @staticmethod
    async def _v1p(path, method='get', auth=False, **params):
        # TODO handle exceptions during sending request
        # TODO handle slowdown exception
        access_id, secret_key = ApiKeys.get_keys()

        # api structure is different with parent class
        url = HTTP_API_BASE_URL + 'perpetual/' + 'v1/' + path
        headers = dict(PerpetualApi._headers)
        if auth:
            if not access_id or not secret_key:
                raise ApiKeyNotSetError('API keys not configured')
            # here are differences with parent _v1 method
            headers['AccessId'] = access_id
            params.update(timestamp=epoch_milliseconds())

        params = collections.OrderedDict(sorted(params.items()))
        if auth:
            headers.update(Authorization=PerpetualApi._sign(params, secret_key))

        async with aiohttp.ClientSession() as session:
            if method == 'post':
                async with session.post(url, data=params, headers=headers) as resp:
                    return PerpetualApi._process_response(await resp.json())
            else:
                async with session.request(method=method, url=url, params=params, headers=headers) as resp:
                    return PerpetualApi._process_response(await resp.json())

    @staticmethod
    def _sign(params, secret_key):
        data = ['='.join([str(k), str(v)]) for k, v in params.items()]
        str_params = "{0}&secret_key={1}".format(
            '&'.join(data), secret_key).encode()
        token = hashlib.sha256(str_params).hexdigest()
        return token

    @classmethod
    async def ping(cls):
        return await cls._v1p('ping', method='get')

    @classmethod
    async def time(cls):
        return await cls._v1p('time', method='get')

    @classmethod
    async def p_market_list(cls):
        return await cls._v1p('market/list', method='get')

    @classmethod
    async def market_limit_config(cls):
        return await cls._v1p('market/limit_config', method='get')

    @classmethod
    async def p_market_ticker(cls, market):
        return await cls._v1p('market/ticker', method='get', market=market)

    @classmethod
    async def p_market_depth(cls, market, merge, limit):
        return await cls._v1p('market/depth', method='get', market=market, merge=merge, limit=limit)

    @classmethod
    async def p_market_deals(cls, market, **params):
        return await cls._v1p('market/deals', method='get', market=market, **params)

    @classmethod
    async def market_funding_history(cls, market, offset, limit, **params):
        return await cls._v1p('market/funding_history', method='get', market=market, offset=offset, limit=limit,
                              **params)

    @classmethod
    async def market_user_deals(cls, market, side, offset, limit, **params):
        return await cls._v1p('market/user_deals', method='get', market=market, side=side, offset=offset, limit=limit,
                              **params)

    @classmethod
    async def p_market_kline(cls, market, type, **params):
        return await cls._v1p('market/kline', method='get', market=market, type=type, **params)

    @classmethod
    async def adjust_leverage(cls, market, leverage, position_type, **params):
        """
        Args:
            position_type (Int): 1 Isolated - 2 Cross
        """
        return await cls._v1p('market/adjust_leverage', method='post', auth=True, market=market,
                              position_type=position_type,
                              leverage=leverage, **params)

    @classmethod
    async def get_position_amount(cls, market, price, side, **params):
        return await cls._v1p('market/position_expect', method='post', auth=True, market=market, price=price, side=side,
                              **params)

    @classmethod
    async def asset_query(cls):
        return await cls._v1p('asset/query', method='get', auth=True)

    @classmethod
    async def put_limit_order(cls, market, amount, price, side, **params):
        return await cls._v1p('order/put_limit', method='post', auth=True, market=market, amount=amount, price=price,
                              side=side, **params)

    @classmethod
    async def put_market_order(cls, market, side, amount, **params):
        return await cls._v1p('order/put_market', method='post', auth=True, market=market, side=side, amount=amount,
                              **params)

    @classmethod
    async def put_stop_limit_order(cls, market, amount, side, price, stop_type, stop_price, **params):
        return await cls._v1p('order/put_stop_limit', method='post', auth=True, market=market, amount=amount, side=side,
                              price=price, stop_type=stop_type, stop_price=stop_price, **params)

    @classmethod
    async def put_stop_market_order(cls, market, amount, side, stop_type, stop_price, **params):
        return await cls._v1p('order/put_stop_market', method='post', auth=True, market=market, amount=amount,
                              side=side,
                              stop_type=stop_type, stop_price=stop_price, **params)

    @classmethod
    async def put_limit_close_order(cls, market, position_id, amount, price, **params):
        return await cls._v1p('order/close_limit', method='post', auth=True, market=market, position_id=position_id,
                              amount=amount, price=price, **params)

    @classmethod
    async def put_market_close_order(cls, market, position_id, **params):
        return await cls._v1p('order/close_market', method='post', auth=True, market=market, position_id=position_id,
                              **params)

    @classmethod
    async def cancel_pending_order(cls, market, order_id, **params):
        return await cls._v1p('order/cancel', method='post', auth=True, market=market, order_id=order_id, **params)

    @classmethod
    async def cancel_pending_order_all(cls, market, **params):
        return await cls._v1p('order/cancel_all', method='post', auth=True, market=market, **params)

    @classmethod
    async def cancel_pending_stop_order(cls, market, order_id, **params):
        return await cls._v1p('order/cancel_stop', method='post', auth=True, market=market, order_id=order_id, **params)

    @classmethod
    async def query_pending_order(cls, market, side, offset, limit, **params):
        return await cls._v1p('order/pending', method='get', auth=True, market=market, side=side, offset=offset,
                              limit=limit,
                              **params)

    @classmethod
    async def query_finished_order(cls, market, side, offset, limit, **params):
        return await cls._v1p('order/finished', method='get', auth=True, market=market, side=side, offset=offset,
                              limit=limit,
                              **params)

    @classmethod
    async def query_stop_order(cls, market, side, offset, limit, **params):
        return await cls._v1p('order/stop_pending', method='get', auth=True, market=market, side=side, offset=offset,
                              limit=limit, **params)

    @classmethod
    async def query_order_status(cls, market, order_id, **params):
        return await cls._v1p('order/status', method='get', auth=True, market=market, order_id=order_id, **params)

    @classmethod
    async def query_pending_position(cls, **params):
        return await cls._v1p('position/pending', method='get', auth=True, **params)

    @classmethod
    async def adjust_position_margin(cls, market, amount, type, **params):
        return await cls._v1p('position/adjust_margin', method='post', auth=True, market=market, amount=amount,
                              type=type,
                              **params)
