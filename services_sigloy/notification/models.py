import datetime

from sqlalchemy import Column, BigInteger, DateTime, Text, Boolean, ForeignKey

from common.resources.tables import table_names
from db.pgsql.engine import Base


class Notification(Base):
    __tablename__ = table_names["notifications"]

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    data = Column(Text, nullable=False)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now,
                        onupdate=datetime.datetime.now)
    deleted_at = Column(DateTime)
