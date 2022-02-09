from typing import List
from sqlalchemy import update, select
from sqlalchemy.ext.asyncio import AsyncSession

from currencies import models


async def get_currencies(async_session: AsyncSession) -> List[models.Currency]:
    result = await async_session.execute(select(models.Currency))
    return result.scalars().all()


async def get_currency(async_session: AsyncSession, coin_short_name: str) -> models.Currency:
    res = await async_session.execute(select(models.Currency).filter_by(short_name=coin_short_name))
    return res.scalar()


async def create_currency(async_session: AsyncSession, short_name, full_name, networks, markets, rank, is_stable):
    new_currency = models.Currency(short_name=short_name, full_name=full_name, networks=networks, markets=markets,
                                   rank=rank, is_stable=is_stable)
    async_session.add(new_currency)
    await async_session.commit()
    return new_currency


async def update_currency(async_session: AsyncSession, currency: models.Currency, use_orm=False, **columns):
    if use_orm:
        currency.update_columns(**columns)
        await async_session.commit()
        return currency
    else:
        await async_session.execute(
            update(models.Currency).filter_by(short_name=currency.short_name).values(**columns))
        await async_session.commit()


async def delete_currency(async_session: AsyncSession, currency: models.Currency):
    await async_session.delete(currency)
    await async_session.commit()
