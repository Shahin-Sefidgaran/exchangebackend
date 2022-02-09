# TODO we might need models for open orders status
import datetime

from sqlalchemy import Column, BigInteger, String, DateTime

from db.pgsql.engine import Base


class CexKeys(Base):
    __tablename__ = "cex_keys"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, index=True)
    access_id = Column(String(100))
    secret_key = Column(String(100))
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now,
                        onupdate=datetime.datetime.now)
    deleted_at = Column(DateTime)
