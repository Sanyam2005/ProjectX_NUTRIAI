from datetime import datetime
from uuid import uuid4

import base64
import hashlib

import bcrypt
from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from app.deps import DB, CurrentUser, create_access_token
from app.models import Goal, User
from app.schemas.auth import LoginRequest, TokenResponse, UserOut
from app.utils import now_ist

router = APIRouter(prefix="/api/auth", tags=["auth"])


# Bcrypt has a hard 72-byte input limit. Pre-hash with SHA-256 (base64-encoded
# to 44 ASCII chars) so any length password is accepted safely. This is the
# pattern used by Django, Spring Security, and the OWASP cheat sheet.
def _normalize(plain: str) -> bytes:
    raw = plain.encode("utf-8")
    if len(raw) > 72:
        raw = base64.b64encode(hashlib.sha256(raw).digest())
    return raw


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(_normalize(plain), bcrypt.gensalt(rounds=12)).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_normalize(plain), hashed.encode("utf-8"))
    except Exception:
        return False


async def _ensure_default_goal(db, user: User) -> None:
    existing = await db.execute(select(Goal).where(Goal.user_id == user.id))
    if existing.scalar_one_or_none() is None:
        db.add(Goal(user_id=user.id))


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        "nutriai_token",
        token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: DB, response: Response) -> TokenResponse:
    """Single entry-point for all sign-in flows.

    * ``mode=password``  — email + password, verified against ``users.password_hash``.
    * ``mode=signup``    — email + password + name; creates a new user.
    * ``mode=microsoft`` — demo flow that accepts {email, name} directly. Real
                           Entra ID would validate ``id_token`` here.
    * ``mode=guest``     — creates an anonymous account.
    """
    if payload.mode == "signup":
        if not payload.email or not payload.password:
            raise HTTPException(status_code=400, detail="email and password required")
        existing = (await db.execute(select(User).where(User.email == payload.email))).scalar_one_or_none()
        if existing is not None:
            raise HTTPException(status_code=409, detail="An account with that email already exists")
        user = User(
            email=payload.email,
            name=(payload.name or payload.email.split("@", 1)[0]).strip() or "User",
            is_guest=False,
            password_hash=_hash_password(payload.password),
        )
        db.add(user)
        await db.flush()
        await _ensure_default_goal(db, user)

    elif payload.mode == "password":
        if not payload.email or not payload.password:
            raise HTTPException(status_code=400, detail="email and password required")
        user = (await db.execute(select(User).where(User.email == payload.email))).scalar_one_or_none()
        if user is None or not user.password_hash:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if not _verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        await _ensure_default_goal(db, user)

    elif payload.mode == "microsoft":
        if not payload.email or not payload.name:
            raise HTTPException(status_code=400, detail="email and name required for microsoft mode")
        existing = await db.execute(select(User).where(User.email == payload.email))
        user = existing.scalar_one_or_none()
        if user is None:
            user = User(
                email=payload.email,
                name=payload.name,
                is_guest=False,
            )
            db.add(user)
            await db.flush()
            await _ensure_default_goal(db, user)

    else:  # guest
        guest_email = f"guest-{uuid4().hex[:8]}@nutriai.local"
        user = User(
            email=guest_email,
            name="Guest",
            is_guest=True,
        )
        db.add(user)
        await db.flush()
        await _ensure_default_goal(db, user)

    user.last_login_at = now_ist()
    await db.commit()
    await db.refresh(user)

    token = create_access_token(subject=user.id, extra={"email": user.email, "guest": user.is_guest})
    _set_session_cookie(response, token)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> Response:
    response.delete_cookie("nutriai_token")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)
