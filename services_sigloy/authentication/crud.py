from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import select, update, desc

from authentication import models
from authentication.models import ForgetTypes
from db.redis.handler import redis_del_key
from db.redis.namespaces import auth_userinfo_namespace


async def get_user(async_session: AsyncSession, username: str) -> models.User:
    result = await async_session.execute(select(models.User).filter_by(username=username))
    return result.scalar()


async def create_user(async_session: AsyncSession, email: str, username: str, token: str, token_expires_at: datetime,
                      hashed_password: str) -> models.User:
    new_user = models.User(email=email, username=username, token=token,
                           token_expires_at=token_expires_at, hashed_password=hashed_password)
    async_session.add(new_user)
    await async_session.commit()
    return new_user


async def update_user(async_session: AsyncSession, user: models.User, use_orm=False, **columns, ) -> models.User:
    """If set true "use_orm" argument, you need to pass the same session as you retrieved object with.
        If you set it false the update command doesn't return any row after execution.
    """
    # delete user from cache
    await redis_del_key(auth_userinfo_namespace, user.username)

    if use_orm:
        user.update_columns(**columns)
        await async_session.commit()
        return user
    else:
        await async_session.execute(update(models.User).filter_by(
            username=user.username).values(**columns))
        await async_session.commit()


async def get_verification_rec_by_user_id(async_session: AsyncSession, user: models.User, code,
                                          verify_type: models.VerificationTypes) -> models.Verification:
    result = await async_session.execute(
        select(models.Verification).filter_by(user_id=user.id, code=code, verify_type=verify_type)
            .order_by(desc(models.Verification.created_at)))
    return result.scalar()


async def get_verification_rec_by_code(async_session: AsyncSession, code,
                                       verify_type: models.VerificationTypes) -> models.Verification:
    """returns verification record by code"""
    result = await async_session.execute(
        select(models.Verification).filter_by(code=code, verify_type=verify_type).order_by(
            desc(models.Verification.created_at)))
    return result.scalar()


async def save_verification(async_session: AsyncSession, user: models.User,
                            verify_type: models.VerificationTypes, code: str):
    new_record = models.Verification(user_id=user.id, verify_type=verify_type, code=code)
    async_session.add(new_record)
    await async_session.commit()
    return new_record


async def delete_verification(async_session: AsyncSession, verification_record: models.Verification):
    async with async_session.begin():  # auto commit
        await async_session.delete(verification_record)


async def create_cex_account(async_session: AsyncSession, **kwargs):
    """create a new cex account"""
    cex_acc = models.CexAccount(**kwargs)
    async_session.add(cex_acc)
    await async_session.commit()
    return cex_acc


async def get_cex_account(async_session: AsyncSession, user: models.User) -> models.CexAccount:
    result = await async_session.execute(select(models.CexAccount).filter_by(user_id=user.id))
    return result.scalar()


async def get_a_free_cex_account(async_session: AsyncSession) -> models.CexAccount:
    result = await async_session.execute(select(models.CexAccount).filter_by(user_id=None))
    return result.scalar()


async def associate_cex_acc_to_user(async_session: AsyncSession,
                                    cex_account: models.CexAccount, user: models.User):
    cex_account.user_id = user.id
    await async_session.commit()


async def create_forget_request(async_session: AsyncSession, user: models.User, forget_type: ForgetTypes,
                                answers: str, file_id: str = None):
    new_request = models.ForgetRequest(user_id=user.id, forget_type=forget_type, answers=answers, file_id=file_id)
    async_session.add(new_request)
    await async_session.commit()
    return new_request


async def create_new_login_history(async_session: AsyncSession, user: models.User,
                                   device, ip, agent, city, region, country):
    new_login = models.LoginHistory(user_id=user.id, device=device, ip=ip,
                                    agent=agent, city=city, region=region, country=country)
    async_session.add(new_login)
    await async_session.commit()
    return new_login


async def get_login_history(async_session: AsyncSession, user: models.User, offset: int = 0, limit: int = 10):
    result = await async_session.execute(
        select(models.LoginHistory).filter_by(user_id=user.id)
            .order_by(desc(models.LoginHistory.created_at)).offset(offset).limit(limit))
    return result.scalars().all()

