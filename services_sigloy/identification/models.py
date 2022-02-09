import datetime
import enum

from sqlalchemy import String, Column, BigInteger, Date, DateTime, SmallInteger, ForeignKey, Enum, Text

from common.resources.tables import table_names
from db.pgsql.engine import Base


class InfoStatuses(enum.Enum):
    not_applied = 0
    okay = 1
    need_change = 2
    rejected = 3


class UserInfo(Base):
    """All information related to user for ID verification"""
    __tablename__ = table_names["user_info"]

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))

    first_name = Column(String(80), nullable=True)
    last_name = Column(String(80), nullable=True)
    birth_day = Column(Date, nullable=True)
    vip_level = Column(SmallInteger, default=0)

    country = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    postal_code = Column(String(30), nullable=True)
    telephone = Column(String(20), nullable=True)
    national_id = Column(String(50), nullable=True)
    passport_number = Column(String(50), nullable=True)
    status = Column(Enum(InfoStatuses), default=InfoStatuses.not_applied)
    review_message = Column(Text(), nullable=True)

    verify_image = Column(String(100), nullable=True)
    id_image = Column(String(100), nullable=True)
    passport_image = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now,
                        onupdate=datetime.datetime.now)
    deleted_at = Column(DateTime)

    def update_columns(self, **columns):
        for key, value in columns.items():
            setattr(self, key, value)

    def __repr__(self):
        return "{}({!r})".format(self.__class__.__name__, self.__dict__)
