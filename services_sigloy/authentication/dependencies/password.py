from fastapi import Depends
from passlib.context import CryptContext

from authentication.schemas import NewPasswords

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    """Check the password with its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """Hashes the password"""
    return pwd_context.hash(password)


def check_new_passwords(new_passwords: NewPasswords):
    """Checks two passwords are the same or not by using pydantic validators"""
    return new_passwords.new_password


def hash_new_password(new_password: str = Depends(check_new_passwords)):
    """First checks passwords are the same by using dependency then tries to
    hash the password."""
    return get_password_hash(new_password)
