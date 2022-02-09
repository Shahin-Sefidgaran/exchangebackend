from typing import Optional

from pydantic import BaseModel, constr


class CexKeysIn(BaseModel):
    user_id: int
    access_id: constr(min_length=30, max_length=35)
    secret_key: constr(min_length=45, max_length=55)

    class Config:
        orm_mode = True


class CoreRequestSchema(BaseModel):
    # TODO do more validations
    target_func: str
    user_id: Optional[int]
    args: dict
    req_time: float
