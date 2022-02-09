import asyncio
import datetime
from random import randint

from sqlalchemy import Boolean, Column, String, BigInteger, Date, DateTime, SmallInteger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost/sigloy"
# SQLALCHEMY_DATABASE_URL = "mysql+aiomysql://alireza:-@localhost/sigloy"

engine = create_async_engine(SQLALCHEMY_DATABASE_URL,
                             echo=True
                             )
AsyncSession = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    email = Column(String(150), unique=True, nullable=False)
    username = Column(String(80), unique=True, index=True, nullable=True)
    mobile = Column(String(12), unique=True)
    token = Column(String(255), nullable=False)
    first_name = Column(String(80))
    last_name = Column(String(80))
    birth_day = Column(Date)
    auth_level = Column(SmallInteger, default=0)
    g_auth_key = Column(String(300))
    vip_level = Column(SmallInteger, default=0)
    secret_key = Column(String(300))
    access_key = Column(String(300))
    hashed_password = Column(String(300), nullable=False)
    is_active = Column(Boolean, default=True)
    token_expires_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now,
                        onupdate=datetime.datetime.now)
    deleted_at = Column(DateTime)


async def send_queries(j):
    rndint = randint(54268, 912542)
    async with AsyncSession() as session:
        new_user = User(email=f'{rndint}email{j}@gmail.com', username=f'{rndint}user{j}',
                        token=f'{rndint}12312312331{j}',
                        token_expires_at=datetime.datetime.now(), hashed_password='hashed_password')
        session.add(new_user)
        await session.commit()


async def async_main():
    await asyncio.gather(*[send_queries(j) for j in range(10000)])


asyncio.run(async_main())
