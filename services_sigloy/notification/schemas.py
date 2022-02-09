from datetime import datetime

from pydantic import BaseModel


class Message(BaseModel):
    """This class that represents a notification message schema"""
    # TODO (PHASE 2) some new attributes might be added to the class
    id: int = None
    data: str


class NotificationOut(BaseModel):
    id: int = None
    read: bool
    data: str
    created_at: datetime

    class Config:
        orm_mode = True
