from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.config import settings
from app.database import get_db
from app.models import User, AuthToken, RefreshToken
from app.schemas import (
    RegisterRequest, LoginRequest, TokenResponse, RefreshRequest,
    VerifyEmailRequest, ResendVerificationRequest,
    ForgotPasswordRequest, ResetPasswordRequest,
)
from app.core.security import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    decode_token, generate_capability_token, hash_token,
)
from app.core.ratelimit import RateLimiter, rate_limit
from app.services.email import send_email
from app.services.email.templates import verify_email as verify_email_tmpl, reset_password as reset_password_tmpl

router = APIRouter()

VERIFY = "verify_email"
RESET = "reset_password"

login_limiter = RateLimiter("login", settings.LOGIN_RATE_LIMIT, settings.RATE_LIMIT_WINDOW_SECONDS)
register_limiter = RateLimiter("register", settings.REGISTER_RATE_LIMIT, settings.RATE_LIMIT_WINDOW_SECONDS)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def _issue_refresh(db: AsyncSession, user: User) -> str:
    """Issue a refresh token and record its jti so it can be rotated/revoked."""
    jti = uuid4().hex
    db.add(RefreshToken(
        user_id=user.id,
        jti=jti,
        expires_at=_utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    ))
    return create_refresh_token({"sub": user.id}, jti=jti)


async def _issue_token(db: AsyncSession, user: User, purpose: str, ttl_hours: int) -> str:
    """Create a single-use auth token, persist only its hash, return the raw token."""
    raw = generate_capability_token()
    db.add(AuthToken(
        user_id=user.id,
        purpose=purpose,
        token_hash=hash_token(raw),
        expires_at=_utcnow() + timedelta(hours=ttl_hours),
    ))
    return raw


async def _consume_token(db: AsyncSession, raw: str, purpose: str) -> AuthToken:
    result = await db.execute(
        select(AuthToken).where(
            AuthToken.token_hash == hash_token(raw),
            AuthToken.purpose == purpose,
        )
    )
    token = result.scalar_one_or_none()
    if token is None or token.used_at is not None or token.expires_at < _utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    token.used_at = _utcnow()
    return token


async def _send_verification(db: AsyncSession, user: User) -> None:
    raw = await _issue_token(db, user, VERIFY, settings.VERIFY_TOKEN_EXPIRE_HOURS)
    subject, html = verify_email_tmpl(f"{settings.FRONTEND_URL}/verify-email?token={raw}")
    send_email(to=user.email, subject=subject, html=html)


@router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(register_limiter))],
)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        role=payload.role,
        church_id=payload.church_id,
    )
    db.add(user)
    await db.flush()
    await _send_verification(db, user)
    refresh_token = await _issue_refresh(db, user)
    await db.commit()
    await db.refresh(user)

    return TokenResponse(
        access_token=create_access_token({"sub": user.id}),
        refresh_token=refresh_token,
        user_id=user.id,
        role=user.role,
    )


@router.post("/verify-email")
async def verify_email(payload: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    token = await _consume_token(db, payload.token, VERIFY)
    result = await db.execute(select(User).where(User.id == token.user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user.email_verified = True
    await db.commit()
    return {"status": "verified"}


@router.post("/resend-verification")
async def resend_verification(payload: ResendVerificationRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    # Always 200 — don't reveal whether an email is registered.
    if user is not None and not user.email_verified:
        await _send_verification(db, user)
        await db.commit()
    return {"status": "sent"}


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    # Always 200 — no account enumeration.
    if user is not None:
        raw = await _issue_token(db, user, RESET, settings.RESET_TOKEN_EXPIRE_HOURS)
        subject, html = reset_password_tmpl(f"{settings.FRONTEND_URL}/reset-password?token={raw}")
        send_email(to=user.email, subject=subject, html=html)
        await db.commit()
    return {"status": "sent"}


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    token = await _consume_token(db, payload.token, RESET)
    result = await db.execute(select(User).where(User.id == token.user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user.password_hash = hash_password(payload.new_password)
    await db.commit()
    return {"status": "reset"}


@router.post(
    "/login", response_model=TokenResponse,
    dependencies=[Depends(rate_limit(login_limiter))],
)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    refresh_token = await _issue_refresh(db, user)
    await db.commit()

    return TokenResponse(
        access_token=create_access_token({"sub": user.id}),
        refresh_token=refresh_token,
        user_id=user.id,
        role=user.role,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    data = decode_token(payload.refresh_token)
    if not data or data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    jti = data.get("jti")
    if not jti:
        # Pre-rotation tokens (no jti) are no longer accepted — force re-login.
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    row = (await db.execute(select(RefreshToken).where(RefreshToken.jti == jti))).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if row.revoked:
        # A rotated/consumed token is being replayed — treat as theft and revoke
        # the whole family so a stolen refresh token can't outlive detection.
        await db.execute(
            update(RefreshToken).where(RefreshToken.user_id == row.user_id).values(revoked=True)
        )
        await db.commit()
        raise HTTPException(status_code=401, detail="Refresh token reuse detected")

    if row.expires_at < _utcnow():
        raise HTTPException(status_code=401, detail="Refresh token expired")

    user = (await db.execute(select(User).where(User.id == row.user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Rotate: revoke the presented token, issue a fresh pair.
    row.revoked = True
    refresh_token = await _issue_refresh(db, user)
    await db.commit()

    return TokenResponse(
        access_token=create_access_token({"sub": user.id}),
        refresh_token=refresh_token,
        user_id=user.id,
        role=user.role,
    )


@router.get("/me")
async def me(db: AsyncSession = Depends(get_db), token: str = ""):
    # Lightweight me endpoint — auth handled via dependency in real requests
    return {"status": "authenticated"}
