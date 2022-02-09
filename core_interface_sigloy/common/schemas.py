from typing import Any

from pydantic import BaseModel


class ResponseSchema(BaseModel):
    status: str = "ok"
    data: Any = {}
    errors = []

    class Config:
        orm_mode = True


