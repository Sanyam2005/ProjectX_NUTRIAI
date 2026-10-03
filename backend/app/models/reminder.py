from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils import now_ist


def _uuid() -> str:
    return str(uuid.uuid4())


class ReminderSettings(Base):
    """One row per user — the user's personal reminder preferences.

    Times are stored as `HH:MM` strings so the FE can render and submit them
    without timezone gymnastics; the FE schedules local browser notifications.
    """
    __tablename__ = "reminder_settings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )

    breakfast_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    breakfast_time: Mapped[str] = mapped_column(String(5), default="08:30")

    lunch_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    lunch_time: Mapped[str] = mapped_column(String(5), default="13:00")

    dinner_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    dinner_time: Mapped[str] = mapped_column(String(5), default="20:00")

    water_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    water_every_min: Mapped[int] = mapped_column(Integer, default=120)

    log_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    log_time: Mapped[str] = mapped_column(String(5), default="21:30")

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_ist, onupdate=now_ist)
