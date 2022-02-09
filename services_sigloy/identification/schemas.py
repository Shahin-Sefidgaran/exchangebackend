import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from identification.models import InfoStatuses


class UserInfoOut(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[str]
    birth_day: Optional[datetime.date]
    vip_level: int
    country: Optional[str]
    region: Optional[str]
    city: Optional[str]
    postal_code: Optional[str]
    telephone: Optional[str]
    national_id: Optional[str]
    passport_number: Optional[str]
    status: InfoStatuses
    review_message: Optional[str]
    verify_image: Optional[str]
    id_image: Optional[str]
    passport_image: Optional[str]

    class Config:
        orm_mode = True
