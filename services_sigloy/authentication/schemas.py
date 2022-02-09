# pydantic models will be placed here
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, validator, constr
from pydantic.networks import EmailStr

from authentication.models import UserStatuses
from common.resources import response_strings


class BaseUser(BaseModel):
    class Config:
        orm_mode = True


class UserAuth(BaseUser):
    username: constr(strip_whitespace=True, to_lower=True,
                     min_length=5, max_length=50)
    password: constr(min_length=8, max_length=50)


class UserScheme(BaseUser):
    id: int
    email: Optional[str]
    username: str
    mobile: Optional[str]
    mobile_auth_enabled: bool
    token: str
    auth_level: int
    two_fa_secret_key: Optional[str]
    two_fa_enabled: bool
    secret_key: Optional[str]
    access_key: Optional[str]
    hashed_password: str
    status: UserStatuses
    token_expires_at: Optional[datetime]
    role: Optional[str]
    referral_code: Optional[str]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]


class UserOut(BaseUser):
    email: str
    username: EmailStr
    mobile: Optional[str] = ...
    # This is not usefull to send, it's just consuming net bandwith
    # token: str
    auth_level: int
    token_expires_at: datetime


class UserRegister(BaseUser):
    username: EmailStr
    # TODO (PHASE 2) change password policies later
    password: constr(min_length=8, max_length=50)


class NewPasswords(BaseModel):
    # TODO (PHASE 2) change password policies later
    new_password: constr(min_length=8, max_length=50)
    new_password_confirm: constr(min_length=8, max_length=50)

    @validator('new_password_confirm')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError(response_strings.PASSWORDS_NOT_MATCH)
        return v


class Verify2FA(BaseModel):
    username: EmailStr
    email_code: Optional[constr(min_length=6, max_length=6)]
    two_fa_code: Optional[constr(max_length=6, min_length=6)]
    tmp_token: constr(min_length=32, max_length=32)


class Get2FA(BaseModel):
    two_fa_code: Optional[constr(max_length=6, min_length=6)]


class ForgetInputs(BaseModel):
    username: EmailStr
    answers: List[str]


class LoginHistoryOut(BaseUser):
    device: str
    ip: str
    city: str
    region: str
    country: str
    created_at: datetime

    class Config:
        orm_mode = True
