from db.pgsql.engine import AsyncDBSession


async def get_db_session():
    db_async_session = AsyncDBSession()
    try:
        yield db_async_session
    finally:
        # closes session automatically after response
        await db_async_session.close()
