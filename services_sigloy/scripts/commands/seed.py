from datetime import timedelta, datetime

from passlib.context import CryptContext

from authentication.crud import create_user, update_user, create_cex_account
from authentication.models import UserStatuses
from db.pgsql.engine import AsyncDBSession
from settings import settings
from currencies.crud import create_currency

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
access_id = 'DF206DBE5678439EBDDBD066534A70E0'
secret_key = 'BA0C859BAFE765A5DC674F9868E7CCCE9941DD0A9C849CB5'


async def seed():
    """Create some records to test the app"""
    exp_at = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    async with AsyncDBSession() as async_session:
        user = await create_user(async_session, 'test@test.com', 'test@test.com', '', exp_at,
                                 pwd_context.hash('test1234'))
        user = await update_user(async_session, user, use_orm=True, status=UserStatuses.active)
        await create_cex_account(async_session, email='test@test.com', hashed_password='asdfsakf',
                                 access_id=access_id, secret_key=secret_key, user_id=user.id)
        await create_cex_account(async_session, email='test1@test.com', hashed_password='asdfsakf',
                                 access_id='access_id', secret_key='secret_key')
        await create_currency(async_session, short_name="USDT", full_name="Tether", networks="ERC20,TRC20,BSC", markets="",
                              rank=999, is_stable=True)
        await create_currency(async_session, short_name="BTC", full_name="Bitcoin", networks="BTC", markets="btcusdt",
                              rank=1, is_stable=False)
