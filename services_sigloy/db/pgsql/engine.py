from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from settings import settings

engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URL, echo=False)

AsyncDBSession = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()
