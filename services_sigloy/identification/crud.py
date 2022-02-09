from sqlalchemy import update, select
from sqlalchemy.ext.asyncio import AsyncSession

from identification import models


async def get_user_info(async_session: AsyncSession, user_id: int) -> models.UserInfo:
    result = await async_session.execute(select(models.UserInfo).filter_by(user_id=user_id))
    return result.scalar()


async def create_user_info(async_session: AsyncSession, **kwargs) -> models.UserInfo:
    new_info = models.UserInfo(**kwargs)
    async_session.add(new_info)
    await async_session.commit()
    return new_info


async def update_user_info(async_session: AsyncSession, user_info: models.UserInfo, use_orm=False,
                           **columns) -> models.UserInfo:
    """If set true "use_orm" argument, you need to pass the same session as you retrieved object with.
        If you set it false the update command doesn't return any row after execution.
    """
    if use_orm:
        user_info.update_columns(**columns)
        await async_session.commit()
        return user_info
    else:
        await async_session.execute(update(models.UserInfo).filter_by(
            id=user_info.id).values(**columns))
        await async_session.commit()
