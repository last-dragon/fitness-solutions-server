from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, root_validator

from fitness_solutions_server.core.models import Sex
from fitness_solutions_server.core.schemas import TimestampMixin


class FitnessCoachBase(BaseModel):
    full_name: str = Field(min_length=2)
    email: EmailStr
    title: str
    description: str
    sex: Sex
    is_released: bool


class FitnessCoachCreate(FitnessCoachBase):
    countries: set[UUID]
    profile_image_id: UUID
    is_released: bool


class FitnessCoachUpdate(BaseModel):
    full_name: str | None = Field(min_length=2)
    email: EmailStr | None
    title: str | None
    description: str | None
    sex: Sex | None
    profile_image_id: UUID | None
    is_released: bool | None


class FitnessCoach(FitnessCoachBase, TimestampMixin):
    id: UUID
    # activated_at: datetime | None
    profile_image_url: str
    number_of_workouts: int
    number_of_fitness_plans: int

    class Config:
        orm_mode = True


class FitnessCoachActivateRequest(BaseModel):
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


class FitnessCoachLoginRequest(BaseModel):
    email: str
    password: str


class FitnessCoachLoginResponse(BaseModel):
    token: str
    fitness_coach: FitnessCoach
