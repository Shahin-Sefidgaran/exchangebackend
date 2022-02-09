from sqlalchemy import update, select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from authentication.shared.classes import ThisUser
from notification import models


async def create_notification(async_session: AsyncSession, **kwargs) -> models.Notification:
    new_notification = models.Notification(**kwargs)
    async_session.add(new_notification)
    await async_session.commit()
    return new_notification


async def get_notification(async_session: AsyncSession, notification_id: int) -> models.Notification:
    result = await async_session.execute(select(models.Notification).filter_by(id=notification_id))
    return result.scalar()


async def mark_as_read_notification(async_session: AsyncSession, notification_id: int):
    await async_session.execute(update(models.Notification).filter_by(
        id=notification_id).values(read=True))
    await async_session.commit()


async def mark_as_read_all_notification(async_session: AsyncSession, user_id: int):
    await async_session.execute(update(models.Notification).filter_by(
        user_id=user_id).values(read=True))
    await async_session.commit()


async def get_new_notifications(async_session: AsyncSession, user: ThisUser, offset: int = 0, limit: int = 10):
    result = await async_session.execute(
        select(models.Notification).filter_by(user_id=user.id)
            .order_by(desc(models.Notification.created_at)).offset(offset).limit(limit))
    return result.scalars().all()
