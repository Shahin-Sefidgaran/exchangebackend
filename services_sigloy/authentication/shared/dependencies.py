from fastapi import Depends

from authentication import models
from authentication.dependencies.auth import get_current_active_user, get_user
from authentication.shared.classes import ThisUser


async def this_user(current_user: models.User = Depends(get_current_active_user)) -> ThisUser:
    """This is a shared function for get_current_active_user dependency at auth deps."""
    return current_user


async def get_this_user(username: str) -> ThisUser:
    """Return user object with this username or None"""
    return await get_user(username)
