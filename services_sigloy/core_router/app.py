import time
from typing import Optional

from fastapi import APIRouter, Body, Depends
from fastapi.responses import ORJSONResponse
from authentication import models
from authentication.dependencies.auth import get_current_active_user
from core_router.network import if_http_request
from core_router.routes import core_routes
from settings import settings

# TODO (PHASE) throttle these routes
core_router = APIRouter(
    prefix="/core",
    tags=["Core Operations"],
    dependencies=[])


async def forward(core_route: str, user_id: int = None, args=None, ORJSONRes=True):
    data = {'target_func': core_route, 'user_id': user_id, 'args': args if args is not None else {},
            'req_time': time.time()}
    response = await if_http_request(settings.CORE_URL + settings.CORE_HANDLER_URI, 'post', data)
    return ORJSONResponse(content=response) if ORJSONRes else response

# TODO (PHASE 2) add input validations


@core_router.get(core_routes['market_list']['uri'])
async def market_list():
    return await forward('market_list')


@core_router.get(core_routes['market_ticker']['uri'])
async def market_ticker(market: str):
    args = {'market': market}
    return await forward('market_ticker', None, args)


@core_router.get(core_routes['market_ticker_all']['uri'])
async def market_ticker_all():
    return await forward('market_ticker_all')


@core_router.get(core_routes['market_depth']['uri'])
async def market_depth(market: str, merge):
    args = {'market': market, 'merge': merge}
    return await forward('market_depth', None, args)


@core_router.get(core_routes['market_deals']['uri'])
async def market_deals(market: str):
    args = {'market': market}
    return await forward('market_deals', None, args)


@core_router.get(core_routes['market_kline']['uri'])
async def market_kline(market: str, type):
    args = {'market': market, 'type': type}
    return await forward('market_kline', None, args)


@core_router.get(core_routes['market_info']['uri'])
async def market_info():
    return await forward('market_info')


@core_router.get(core_routes['market_detail']['uri'])
async def market_detail(market):
    args = {'market': market}
    return await forward('market_detail', None, args)


@core_router.get(core_routes['amm_market']['uri'])
async def amm_market(market, current_user: models.User = Depends(get_current_active_user)):
    args = {'market': market}
    return await forward('amm_market', current_user.id, args)


@core_router.post(core_routes['order_limit']['uri'])
async def order_limit(market: str = Body(...), type=Body(...), amount=Body(...), price=Body(...),
                      current_user: models.User =
                      Depends(get_current_active_user)):
    args = {'market': market, 'type': type, 'amount': amount, 'price': price}
    return await forward('order_limit', current_user.id, args)


@core_router.post(core_routes['order_stop_limit']['uri'])
async def order_stop_limit(market: str = Body(...), type=Body(...), amount=Body(...), price=Body(...), stop_price=Body(...),
                           current_user: models.User =
                           Depends(get_current_active_user)):
    args = {'market': market, 'type': type, 'amount': amount,
            'price': price, 'stop_price': stop_price}
    return await forward('order_stop_limit', current_user.id, args)


@core_router.post(core_routes['order_limit_batch']['uri'])
async def order_limit_batch(market: str, type=Body(...), amount=Body(...), price=Body(...), batch_orders=Body(...),
                            current_user: models.User =
                            Depends(get_current_active_user)):
    args = {'market': market, 'type': type, 'amount': amount,
            'price': price, 'batch_orders': batch_orders}
    return await forward('order_limit_batch', current_user.id, args)


@core_router.post(core_routes['order_market']['uri'])
async def order_market(market: str, type=Body(...), amount=Body(...),
                       current_user: models.User = Depends(get_current_active_user)):
    args = {'market': market, 'type': type, 'amount': amount}
    return await forward('order_market', current_user.id, args)


@core_router.post(core_routes['order_ioc']['uri'])
async def order_ioc(market: str, type=Body(...), amount=Body(...), price=Body(...),
                    current_user: models.User = Depends(get_current_active_user)):
    args = {'market': market, 'type': type, 'amount': amount, 'price': price}
    return await forward('order_ioc', current_user.id, args)


@core_router.get(core_routes['order_pending']['uri'])
async def order_pending(*, market: Optional[str] = None, page, limit,
                        current_user: models.User = Depends(get_current_active_user)):
    args = {'page': page, 'limit': limit}

    if market:
        args.update({'market': market})

    return await forward('order_pending', current_user.id, args)


@core_router.get(core_routes['order_finished']['uri'])
async def order_finished(*, market: Optional[str] = None, page, limit,
                        current_user: models.User = Depends(get_current_active_user)):
    args = {'page': page, 'limit': limit}

    if market:
        args.update({'market': market})

    return await forward('order_finished', current_user.id, args)


@core_router.get(core_routes['order_status']['uri'])
async def order_status(market: str, id, current_user: models.User = Depends(get_current_active_user)):
    args = {'market': market, 'id': id}
    return await forward('order_status', current_user.id, args)


@core_router.get(core_routes['order_status_batch']['uri'])
async def order_status_batch(market: str, batch_ids, current_user: models.User = Depends(get_current_active_user)):
    args = {'market': market, 'batch_ids': batch_ids}
    return await forward('order_status_batch', current_user.id, args)


@core_router.get(core_routes['order_deals']['uri'])
async def order_deals(id, page, limit, current_user: models.User = Depends(get_current_active_user)):
    args = {'id': id, 'page': page, 'limit': limit}
    return await forward('order_deals', current_user.id, args)


@core_router.get(core_routes['order_user_deals']['uri'])
async def order_user_deals(market: str, page, limit, current_user: models.User = Depends(get_current_active_user)):
    args = {'market': market, 'page': page, 'limit': limit}
    return await forward('order_user_deals', current_user.id, args)


@core_router.delete(core_routes['order_pending_cancel']['uri'])
async def order_pending_cancel(market: str, id, current_user: models.User = Depends(get_current_active_user)):
    args = {'market': market, 'id': id}
    return await forward('order_pending_cancel', current_user.id, args)


@core_router.delete(core_routes['order_pending_cancel_batch']['uri'])
async def order_pending_cancel_batch(market: str, batch_ids,
                                     current_user: models.User = Depends(get_current_active_user)):
    args = {'market': market, 'batch_ids': batch_ids}
    return await forward('order_pending_cancel_batch', current_user.id, args)


@core_router.delete(core_routes['order_pending_cancel_all']['uri'])
async def order_pending_cancel_all(account_id, market, current_user: models.User = Depends(get_current_active_user)):
    args = {'account_id': account_id, 'market': market}
    return await forward('order_pending_cancel_all', current_user.id, args)


@core_router.get(core_routes['order_mining_difficulty']['uri'])
async def order_mining_difficulty(current_user: models.User =
                                  Depends(get_current_active_user)):
    return await forward('order_mining_difficulty', current_user.id)


@core_router.get(core_routes['credit_account_info']['uri'])
async def credit_account_info(current_user: models.User =
                              Depends(get_current_active_user)):
    return await forward('credit_account_info', current_user.id)


@core_router.get(core_routes['balance_info']['uri'])
async def balance_info(current_user: models.User =
                       Depends(get_current_active_user)):
    return await forward('balance_info', current_user.id)


@core_router.get(core_routes['balance_coin_withdraw_list']['uri'])
async def balance_coin_withdraw_list(current_user: models.User =
                                     Depends(get_current_active_user)):
    return await forward('balance_coin_withdraw_list', current_user.id)


@core_router.post(core_routes['balance_coin_withdraw']['uri'])
async def balance_coin_withdraw(coin_type=Body(...), coin_address=Body(...),
                                actual_amount=Body(...), transfer_method=Body(...),
                                smart_contract_name=Body(...),
                                current_user: models.User = Depends(get_current_active_user)):
    args = {'coin_type': coin_type, 'coin_address': coin_address, 'actual_amount': actual_amount,
            'transfer_method': transfer_method, 'smart_contract_name': smart_contract_name}
    return await forward('balance_coin_withdraw', current_user.id, args)


@core_router.delete(core_routes['balance_coin_withdraw_cancel']['uri'])
async def balance_coin_withdraw_cancel(coin_withdraw_id, current_user: models.User = Depends(get_current_active_user)):
    args = {'coin_withdraw_id': coin_withdraw_id}
    return await forward('balance_coin_withdraw_cancel', current_user.id, args)


@core_router.get(core_routes['balance_coin_deposit_list']['uri'])
async def balance_coin_deposit_list(current_user: models.User =
                                    Depends(get_current_active_user)):
    return await forward('balance_coin_deposit_list', current_user.id)


@core_router.get(core_routes['balance_deposit_address']['uri'])
async def balance_deposit_address(coin_type, smart_contract_name,
                                  current_user: models.User = Depends(get_current_active_user)):
    args = {'coin_type': coin_type, 'smart_contract_name': smart_contract_name}
    return await forward('balance_deposit_address', current_user.id, args)


@core_router.post(core_routes['balance_deposit_address_new']['uri'])
async def balance_deposit_address_new(coin_type, current_user: models.User = Depends(get_current_active_user)):
    args = {'coin_type': coin_type}
    return await forward('balance_deposit_address_new', current_user.id, args)


@core_router.post(core_routes['sub_account_transfer']['uri'])
async def sub_account_transfer(coin_type: str = Body(...), amount=Body(...),
                               current_user: models.User = Depends(get_current_active_user)):
    args = {'coin_type': coin_type, 'amount': amount}
    return await forward('sub_account_transfer', current_user.id, args)


@core_router.get(core_routes['sub_account_balance']['uri'])
async def sub_account_balance(current_user: models.User =
                              Depends(get_current_active_user)):
    return await forward('sub_account_balance', current_user.id)


@core_router.get(core_routes['sub_account_transfer_history']['uri'])
async def sub_account_transfer_history(current_user: models.User =
                                       Depends(get_current_active_user)):
    return await forward('sub_account_transfer_history', current_user.id)


@core_router.post(core_routes['margin_transfer']['uri'])
async def margin_transfer(from_account=Body(...), to_account=Body(...), coin_type=Body(...), amount=Body(...),
                          current_user: models.User =
                          Depends(get_current_active_user)):
    args = {'from_account': from_account, 'to_account': to_account,
            'coin_type': coin_type, 'amount': amount}
    return await forward('margin_transfer', current_user.id, args)


@core_router.get(core_routes['margin_account']['uri'])
async def margin_account(current_user: models.User =
                         Depends(get_current_active_user)):
    return await forward('margin_account', current_user.id)


@core_router.get(core_routes['margin_account_currency']['uri'])
async def margin_account_currency(market, current_user: models.User = Depends(get_current_active_user)):
    args = {'market': market}
    return await forward('margin_account_currency', current_user.id, args)


@core_router.get(core_routes['margin_config']['uri'])
async def margin_config(current_user: models.User =
                        Depends(get_current_active_user)):
    return await forward('margin_config', current_user.id)


@core_router.get(core_routes['margin_config_currency']['uri'])
async def margin_config_currency(market, current_user: models.User = Depends(get_current_active_user)):
    args = {'market': market}
    return await forward('margin_config_currency', current_user.id, args)


@core_router.get(core_routes['margin_loan_history']['uri'])
async def margin_loan_history(current_user: models.User =
                              Depends(get_current_active_user)):
    return await forward('margin_loan_history', current_user.id)


@core_router.post(core_routes['margin_loan']['uri'])
async def margin_loan(market: str = Body(...), coin_type=Body(...), amount=Body(...),
                      current_user: models.User = Depends(get_current_active_user)):
    args = {'market': market, 'coin_type': coin_type, 'amount': amount}
    return await forward('margin_loan', current_user.id, args)


@core_router.post(core_routes['margin_flat']['uri'])
async def margin_flat(market: str = Body(...), coin_type=Body(...), amount=Body(...),
                      current_user: models.User = Depends(get_current_active_user)):
    args = {'market': market, 'coin_type': coin_type, 'amount': amount}
    return await forward('margin_flat', current_user.id, args)


@core_router.get(core_routes['currency_rate']['uri'])
async def currency_rate(current_user: models.User =
                        Depends(get_current_active_user)):
    return await forward('currency_rate', current_user.id)


@core_router.get(core_routes['asset_config']['uri'])
async def asset_config(current_user: models.User =
                       Depends(get_current_active_user)):
    return await forward('asset_config', current_user.id)


@core_router.post(core_routes['contract_balance_transfer']['uri'])
async def contract_balance_transfer(coin_type=Body(...), amount=Body(...), transfer_side=Body(...),
                                    current_user: models.User =
                                    Depends(get_current_active_user)):
    args = {'coin_type': coin_type, 'amount': amount,
            'transfer_side': transfer_side}
    return await forward('contract_balance_transfer', current_user.id, args)


@core_router.get(core_routes['ping']['uri'])
async def core_ping():
    return await forward('ping')


@core_router.get(core_routes['time']['uri'])
async def core_time():
    return await forward('time')


@core_router.get(core_routes['p_market_list']['uri'])
async def p_market_list(current_user: models.User =
                        Depends(get_current_active_user)):
    return await forward('market_list', current_user.id)


@core_router.get(core_routes['market_limit_config']['uri'])
async def market_limit_config(current_user: models.User =
                              Depends(get_current_active_user)):
    return await forward('market_limit_config', current_user.id)


@core_router.get(core_routes['p_market_ticker']['uri'])
async def p_market_ticker(market, current_user: models.User = Depends(get_current_active_user)):
    args = {'market': market}
    return await forward('market_ticker', current_user.id, args)


@core_router.get(core_routes['p_market_depth']['uri'])
async def p_market_depth(market: str, merge, limit, current_user: models.User = Depends(get_current_active_user)):
    args = {'market': market, 'merge': merge, 'limit': limit}
    return await forward('market_depth', current_user.id, args)


@core_router.get(core_routes['p_market_deals']['uri'])
async def p_market_deals(market, current_user: models.User = Depends(get_current_active_user)):
    args = {'market': market}
    return await forward('market_deals', current_user.id, args)


@core_router.get(core_routes['market_funding_history']['uri'])
async def market_funding_history(market: str, offset, limit,
                                 current_user: models.User = Depends(get_current_active_user)):
    args = {'market': market, 'offset': offset, 'limit': limit}
    return await forward('market_funding_history', current_user.id, args)


@core_router.get(core_routes['market_user_deals']['uri'])
async def market_user_deals(market: str, side, offset, limit,
                            current_user: models.User = Depends(get_current_active_user)):
    args = {'market': market, 'side': side, 'offset': offset, 'limit': limit}
    return await forward('market_user_deals', current_user.id, args)


@core_router.get(core_routes['p_market_kline']['uri'])
async def p_market_kline(market: str, type, current_user: models.User = Depends(get_current_active_user)):
    args = {'market': market, 'type': type}
    return await forward('market_kline', current_user.id, args)


@core_router.get(core_routes['adjust_leverage']['uri'])
async def adjust_leverage(market: str, leverage, position_type,
                          current_user: models.User = Depends(get_current_active_user)):
    args = {'market': market, 'leverage': leverage,
            'position_type': position_type}
    return await forward('adjust_leverage', current_user.id, args)


@core_router.post(core_routes['get_position_amount']['uri'])
async def get_position_amount(market: str = Body(...), price=Body(...), side=Body(...),
                              current_user: models.User = Depends(get_current_active_user)):
    args = {'market': market, 'price': price, 'side': side}
    return await forward('get_position_amount', current_user.id, args)


@core_router.get(core_routes['asset_query']['uri'])
async def asset_query(current_user: models.User =
                      Depends(get_current_active_user)):
    return await forward('asset_query', current_user.id)


@core_router.post(core_routes['put_limit_order']['uri'])
async def put_limit_order(market: str = Body(...), amount=Body(...), price=Body(...), side=Body(...),
                          current_user: models.User =
                          Depends(get_current_active_user)):
    args = {'market': market, 'amount': amount, 'price': price, 'side': side}
    return await forward('put_limit_order', current_user.id, args)


@core_router.post(core_routes['put_market_order']['uri'])
async def put_market_order(market: str = Body(...), side=Body(...), amount=Body(...),
                           current_user: models.User = Depends(get_current_active_user)):
    args = {'market': market, 'side': side, 'amount': amount}
    return await forward('put_market_order', current_user.id, args)


@core_router.post(core_routes['put_stop_limit_order']['uri'])
async def put_stop_limit_order(market: str, amount=Body(...), side=Body(...), price=Body(...),
                               stop_type=Body(...), stop_price=Body(...), current_user: models.User =
                               Depends(get_current_active_user)):
    args = {'market': market, 'amount': amount, 'side': side, 'price': price, 'stop_type': stop_type,
            'stop_price': stop_price}
    return await forward('put_stop_limit_order', current_user.id, args)


@core_router.post(core_routes['put_stop_market_order']['uri'])
async def put_stop_market_order(market: str = Body(...), amount=Body(...), side=Body(...),
                                stop_type=Body(...), stop_price=Body(...),
                                current_user: models.User = Depends(get_current_active_user)):
    args = {'market': market, 'amount': amount, 'side': side,
            'stop_type': stop_type, 'stop_price': stop_price}
    return await forward('put_stop_market_order', current_user.id, args)


@core_router.post(core_routes['put_limit_close_order']['uri'])
async def put_limit_close_order(market: str = Body(...), position_id=Body(...), amount=Body(...), price=Body(...),
                                current_user: models.User =
                                Depends(get_current_active_user)):
    args = {'market': market, 'position_id': position_id,
            'amount': amount, 'price': price}
    return await forward('put_limit_close_order', current_user.id, args)


@core_router.post(core_routes['put_market_close_order']['uri'])
async def put_market_close_order(market: str = Body(...), position_id=Body(...),
                                 current_user: models.User = Depends(get_current_active_user)):
    args = {'market': market, 'position_id': position_id}
    return await forward('put_market_close_order', current_user.id, args)


@core_router.post(core_routes['cancel_pending_order']['uri'])
async def cancel_pending_order(market: str = Body(...), order_id=Body(...),
                               current_user: models.User = Depends(get_current_active_user)):
    args = {'market': market, 'order_id': order_id}
    return await forward('cancel_pending_order', current_user.id, args)


@core_router.post(core_routes['cancel_pending_order_all']['uri'])
async def cancel_pending_order_all(market=Body(...), current_user: models.User = Depends(get_current_active_user)):
    args = {'market': market}
    return await forward('cancel_pending_order_all', current_user.id, args)


@core_router.post(core_routes['cancel_pending_stop_order']['uri'])
async def cancel_pending_stop_order(market: str = Body(...), order_id=Body(...),
                                    current_user: models.User = Depends(get_current_active_user)):
    args = {'market': market, 'order_id': order_id}
    return await forward('cancel_pending_stop_order', current_user.id, args)


@core_router.get(core_routes['query_pending_order']['uri'])
async def query_pending_order(market: str, side, offset, limit,
                              current_user: models.User = Depends(get_current_active_user)):
    args = {'market': market, 'side': side, 'offset': offset, 'limit': limit}
    return await forward('query_pending_order', current_user.id, args)


@core_router.get(core_routes['query_finished_order']['uri'])
async def query_finished_order(market: str, side, offset, limit,
                               current_user: models.User = Depends(get_current_active_user)):
    args = {'market': market, 'side': side, 'offset': offset, 'limit': limit}
    return await forward('query_finished_order', current_user.id, args)


@core_router.get(core_routes['query_stop_order']['uri'])
async def query_stop_order(market: str, side, offset, limit,
                           current_user: models.User = Depends(get_current_active_user)):
    args = {'market': market, 'side': side, 'offset': offset, 'limit': limit}
    return await forward('query_stop_order', current_user.id, args)


@core_router.get(core_routes['query_order_status']['uri'])
async def query_order_status(market: str, order_id, current_user: models.User = Depends(get_current_active_user)):
    args = {'market': market, 'order_id': order_id}
    return await forward('query_order_status', current_user.id, args)


@core_router.get(core_routes['query_pending_position']['uri'])
async def query_pending_position(current_user: models.User =
                                 Depends(get_current_active_user)):
    return await forward('query_pending_position', current_user.id)


@core_router.post(core_routes['adjust_position_margin']['uri'])
async def adjust_position_margin(market: str = Body(...), amount=Body(...), type=Body(...),
                                 current_user: models.User = Depends(get_current_active_user)):
    args = {'market': market, 'amount': amount, 'type': type}
    return await forward('adjust_position_margin', current_user.id, args)
