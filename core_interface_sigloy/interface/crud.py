from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from interface import models


async def create_cex_keys(async_session: AsyncSession, user_id: int, access_id: str, secret_key: str) -> models.CexKeys:
    new_cex_keys = models.CexKeys(user_id=user_id, access_id=access_id, secret_key=secret_key)
    async_session.add(new_cex_keys)
    await async_session.commit()
    return new_cex_keys


async def get_cex_keys(async_session: AsyncSession, user_id) -> models.CexKeys:
    result = await async_session.execute(select(models.CexKeys).filter_by(user_id=user_id))
    return result.scalar()


async def update_cex_keys(async_session: AsyncSession, cex_keys: models.CexKeys, use_orm=False,
                          **columns, ) -> models.CexKeys:
    """If set true "use_orm" argument, you need to pass the same session as you retrieved object with.
        If you set it false the update command doesn't return any row after execute.
    """
    if use_orm:
        cex_keys.update_columns(**columns)
        await async_session.commit()
        return cex_keys
    else:
        await async_session.execute(update(models.CexKeys).filter_by(
            user_id=cex_keys.user_id).values(**columns))
        await async_session.commit()
