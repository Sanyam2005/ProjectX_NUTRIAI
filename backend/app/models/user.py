from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils import now_ist


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(String(1024), default=None)
    is_guest: Mapped[bool] = mapped_column(Boolean, default=False)
    entra_oid: Mapped[str | None] = mapped_column(String(64), unique=True, default=None)
    password_hash: Mapped[str | None] = mapped_column(String(255), default=None)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_ist)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    meals: Mapped[list["Meal"]] = relationship(back_populates="user", cascade="all, delete-orphan")  # noqa: F821
    goal: Mapped["Goal | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")  # noqa: F821
