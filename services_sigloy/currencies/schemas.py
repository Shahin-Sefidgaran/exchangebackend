from typing import List

from pydantic import BaseModel
from pydantic.types import conint, constr


class CurrencySchema(BaseModel):
    short_name: constr(max_length=6)
    full_name: constr(max_length=16)
    networks: List[str]
    markets: List[str]
    rank: conint(ge=0, le=100000)
    is_stable: bool

    class Config:
        orm_mode = True
