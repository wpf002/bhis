from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://bhis:bhis_dev@localhost:5432/bhis"
    REDIS_URL: str = "redis://localhost:6379"
    SECRET_KEY: str = "dev-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ENVIRONMENT: str = "development"

    # Email — defaults to the in-process console backend so nothing sends by
    # accident. Set EMAIL_BACKEND=sendgrid + SENDGRID_API_KEY in production.
    EMAIL_BACKEND: str = "console"
    EMAIL_FROM: str = "no-reply@bhis.local"
    SENDGRID_API_KEY: str = ""
    FRONTEND_URL: str = "http://localhost:5173"

    # Single-use auth token lifetimes
    VERIFY_TOKEN_EXPIRE_HOURS: int = 24
    RESET_TOKEN_EXPIRE_HOURS: int = 1

    # Rate limiting (per client IP, fixed window in seconds)
    LOGIN_RATE_LIMIT: int = 10
    REGISTER_RATE_LIMIT: int = 5
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # A completed survey faster than this is flagged as a likely bot/low-effort.
    MIN_COMPLETION_SECONDS: int = 120

    class Config:
        env_file = ".env"


settings = Settings()
