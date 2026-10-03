from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils import now_ist


def _uuid() -> str:
    return str(uuid.uuid4())


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)

    weight_kg: Mapped[float | None] = mapped_column(Float, default=None)
    target_weight_kg: Mapped[float | None] = mapped_column(Float, default=None)
    height_cm: Mapped[float | None] = mapped_column(Float, default=None)
    age: Mapped[int | None] = mapped_column(Integer, default=None)
    gender: Mapped[str | None] = mapped_column(String(16), default=None)  # male | female | other
    activity_level: Mapped[str] = mapped_column(String(32), default="moderate")  # sedentary | light | moderate | active | very_active

    target_calories: Mapped[int] = mapped_column(Integer, default=2000)
    target_protein_g: Mapped[int] = mapped_column(Integer, default=80)
    target_carbs_g: Mapped[int] = mapped_column(Integer, default=250)
    target_fat_g: Mapped[int] = mapped_column(Integer, default=65)
    target_fiber_g: Mapped[int] = mapped_column(Integer, default=30)
    target_water_ml: Mapped[int] = mapped_column(Integer, default=2500)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_ist, onupdate=now_ist)

    user: Mapped["User"] = relationship(back_populates="goal")  # noqa: F821
