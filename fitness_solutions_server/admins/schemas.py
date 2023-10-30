from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, root_validator

from fitness_solutions_server.core.schemas import TimestampMixin


class AdminBase(BaseModel):
    full_name: str = Field(min_length=2)
    email: EmailStr


class AdminCreate(AdminBase):
    pass


class Admin(AdminBase, TimestampMixin):
    id: UUID
    activated_at: datetime | None

    class Config:
        orm_mode = True


class AdminActivateRequest(BaseModel):
    password: str = Field(min_length=8, max_length=24)
    confirm_password: str
    activation_token: str

    @root_validator()
    def verify_passwords_match(cls, values):
        password = values.get("password")
        confirm_password = values.get("confirm_password")
        if password != confirm_password:
            raise ValueError("The two passwords did not match.")
        return values


class AdminLoginRequest(BaseModel):
    email: str
    password: str


class AdminLoginResponse(BaseModel):
    token: str
    admin: Admin
