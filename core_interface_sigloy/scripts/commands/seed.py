from datetime import timedelta, datetime

from passlib.context import CryptContext

from db.pgsql.engine import AsyncDBSession
from settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
access_id = '82AD8CBEE85046AFBFF1B7D292EC9757'
secret_key = '9575DC1AF9A09860FFFD90909B61C2C431A520095E9F5E0D'


async def seed():
    """Create some records to test the app"""
    async with AsyncDBSession() as async_session:
        pass