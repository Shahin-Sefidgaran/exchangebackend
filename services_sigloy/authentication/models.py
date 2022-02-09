import datetime
import enum

from sqlalchemy import Column, ForeignKey, String, BigInteger, DateTime, SmallInteger, Enum, Boolean, Text
from sqlalchemy.orm import relationship

from common.resources.tables import table_names
from db.pgsql.engine import Base

"""Models required for authentication"""


class UserStatuses(enum.Enum):
    not_verified = 0
    no_cex_acc = 1
    active = 2
    inactive = 3


class User(Base):
    """Every change in this class results changes to "UserInfo" pydantic schema!
    Don't forget it."""
    __tablename__ = table_names["users"]

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    email = Column(String(150), unique=True, nullable=False)
    username = Column(String(80), unique=True, index=True, nullable=True)  # is email for now
    mobile = Column(String(12), unique=True)
    mobile_auth_enabled = Column(Boolean(), default=0)
    token = Column(String(255), nullable=False)
    auth_level = Column(SmallInteger, default=0)
    two_fa_secret_key = Column(String(300), nullable=True)
    two_fa_enabled = Column(Boolean(), default=0)  # mean g_auth
    secret_key = Column(String(300))
    access_key = Column(String(300))
    hashed_password = Column(String(300), nullable=False)
    status = Column(Enum(UserStatuses), default=UserStatuses.not_verified)
    token_expires_at = Column(DateTime)
    role = Column(String(100), default='user')
    cex_account = relationship(
        'CexAccount', uselist=False, back_populates='user')
    verifications = relationship("Verification", back_populates="user")
    referral_code = Column(String(10), unique=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now,
                        onupdate=datetime.datetime.now)
    deleted_at = Column(DateTime)

    def update_columns(self, **columns):
        for key, value in columns.items():
            setattr(self, key, value)

    def as_dict(self):
        for c in self.__table__.columns:
            print(type(c.type))
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return "{}({!r})".format(self.__class__.__name__, self.__dict__)


class CexAccount(Base):
    __tablename__ = table_names["cex_accounts"]

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    email = Column(String(150), unique=True, nullable=False)
    hashed_password = Column(String(300), nullable=False)
    g_auth_key = Column(String(300))
    session_key = Column(String(300))
    access_id = Column(String(300))
    secret_key = Column(String(300))
    user = relationship(
        'User', uselist=False, back_populates='cex_account')
    user_id = Column(BigInteger, ForeignKey('users.id'), index=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now,
                        onupdate=datetime.datetime.now)
    deleted_at = Column(DateTime)

    def __repr__(self):
        return "{}({!r})".format(self.__class__.__name__, self.__dict__)


class VerificationTypes(enum.Enum):
    register_email_verify = 0
    email_code_verify = 1
    sms_code_verify = 2  # not used for now


class Verification(Base):
    __tablename__ = table_names["verifications"]

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    user = relationship("User", back_populates="verifications", lazy="selectin")
    verify_type = Column(Enum(VerificationTypes))
    code = Column(String(100))
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now,
                        onupdate=datetime.datetime.now)

    def __repr__(self):
        return "{}({!r})".format(self.__class__.__name__, self.__dict__)


class ForgetTypes(enum.Enum):
    two_fa_forget = 0
    email_forget = 1


class ForgetRequest(Base):
    __tablename__ = table_names["forget_requests"]

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    user = relationship("User", lazy="selectin")
    forget_type = Column(Enum(ForgetTypes))
    answers = Column(Text(), nullable=False)
    file_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now,
                        onupdate=datetime.datetime.now)

    def __repr__(self):
        return "{}({!r})".format(self.__class__.__name__, self.__dict__)


class LoginHistory(Base):
    __tablename__ = table_names["login_history"]
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    device = Column(String(200), nullable=True)
    ip = Column(String(20), nullable=True)
    agent = Column(String(300), nullable=True)
    city = Column(String(50), nullable=True)
    region = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)

    def __repr__(self):
        return "{}({!r})".format(self.__class__.__name__, self.__dict__)

# TODO (PHASE 2) create referral table
