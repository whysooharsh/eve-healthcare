from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class SignupIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str


class CentreIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    location: str = Field(min_length=1, max_length=255)


class CentreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    location: str


class TestIn(BaseModel):
    centre_id: int
    name: str = Field(min_length=1, max_length=255)
    price: float = Field(gt=0)


class TestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    centre_id: int
    name: str
    price: float


class CentreDetailOut(CentreOut):
    tests: list[TestOut] = []


class BookingIn(BaseModel):
    test_id: int
    appointment_at: datetime

    @field_validator("appointment_at")
    @classmethod
    def must_be_future(cls, v: datetime) -> datetime:
        if v <= datetime.now(v.tzinfo) if v.tzinfo else datetime.now():
            raise ValueError("appointment_at must be in the future")
        return v


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    test_id: int
    centre_id: int
    appointment_at: datetime
    amount: float
    status: str


class PaymentIn(BaseModel):
    booking_id: int
    succeed: bool = True


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    booking_id: int
    amount: float
    status: str


class WebhookIn(BaseModel):
    event_id: str = Field(min_length=1, max_length=64)
    booking_id: int
    status: str = Field(pattern="^(SUCCESS|FAILED)$")
