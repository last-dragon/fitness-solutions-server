from datetime import timedelta

from pydantic import AnyHttpUrl, BaseSettings, PostgresDsn


class Settings(BaseSettings):
    DATABASE_URL: PostgresDsn
    BASE_URL: AnyHttpUrl

    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_FROM: str
    SMTP_PORT: int
    SMTP_SERVER: str

    USER_AUTH_EXPIRE_DELTA: timedelta = timedelta(days=90)
    ADMIN_AUTH_EXPIRE_DELTA: timedelta = timedelta(days=7)
    FITNESS_COACH_AUTH_EXPIRE_DELTA: timedelta = timedelta(days=7)
    ADMIN_EMAIL: str

    GOOGLE_CLOUD_STORAGE_BUCKET: str
    GOOGLE_CLOUD_PROJECT: str

    class Config:
        env_file = ".env"


settings = Settings()
