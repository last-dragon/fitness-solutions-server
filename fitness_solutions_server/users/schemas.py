from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, root_validator

from fitness_solutions_server.core.schemas import TimestampMixin
from fitness_solutions_server.countries.schemas import Country
from fitness_solutions_server.users.models import Focus, Sex

from typing import Optional


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, title="The full name of the user")
    sex: Sex | None
    height: float | None = Field(gt=0, title="Height", description="Height in cm")
    birthdate: date | None
    focus: Focus | None
    profile_image_id: UUID | None


class UserRegistration(UserBase):
    password: str = Field(min_length=8, max_length=24, title="User password")
    weight: float = Field(gt=0, title="Weight", description="Weight in kg")
    confirm_password: str
    country_id: UUID

    @root_validator()
    def verify_passwords_match(cls, values):
        password = values.get("password")
        confirm_password = values.get("confirm_password")
        if password != confirm_password:
            raise ValueError("The two passwords did not match.")
        return values


class UserUpdate(BaseModel):
    email: EmailStr | None
    full_name: str | None = Field(min_length=2, title="The full name of the user")
    sex: Sex | None = Field(nullable=True)
    height: float | None = Field(
        gt=0, title="Height", description="Height in cm", nullable=True
    )
    birthdate: date | None = Field(nullable=True)
    focus: Focus | None = Field(nullable=True)
    country_id: UUID | None
    profile_image_id: UUID

    class Config:
        orm_mode = True


class User(UserBase, TimestampMixin):
    id: UUID
    verified_at: datetime | None = None
    country: Country
    weight: float | None = Field(gt=0, title="Weight", description="Weight in kg")
    profile_image_url: str | None

    class Config:
        orm_mode = True


class UserRegistrationResponse(BaseModel):
    token: str
    user: User


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserLoginResponse(BaseModel):
    user: User
    token: str


class UserResetPassword(BaseModel):
    verification_token: Optional[str]
