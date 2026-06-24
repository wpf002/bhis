from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://bhis:bhis_dev@localhost:5432/bhis"

    @field_validator("DATABASE_URL")
    @classmethod
    def _ensure_async_driver(cls, v: str) -> str:
        # Hosts like Railway/Render expose Postgres as "postgresql://..."; the app
        # (and alembic, which imports this Settings) needs the asyncpg driver.
        if v.startswith("postgres://"):
            v = "postgresql://" + v[len("postgres://"):]
        if v.startswith("postgresql://") and not v.startswith("postgresql+"):
            v = "postgresql+asyncpg://" + v[len("postgresql://"):]
        return v
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

    # Observability
    SENTRY_DSN: str = ""              # empty → Sentry disabled
    SLOW_REQUEST_MS: int = 2000       # requests slower than this are logged as warnings

    class Config:
        env_file = ".env"


settings = Settings()
