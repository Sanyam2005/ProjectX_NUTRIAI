from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils import now_ist


def _uuid() -> str:
    return str(uuid.uuid4())


class Meal(Base):
    __tablename__ = "meals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)

    name: Mapped[str] = mapped_column(String(255))
    meal_type: Mapped[str] = mapped_column(String(32), default="lunch")  # breakfast | lunch | dinner | snack
    image_url: Mapped[str | None] = mapped_column(String(1024), default=None)
    notes: Mapped[str | None] = mapped_column(Text, default=None)

    consumed_at: Mapped[datetime] = mapped_column(DateTime, default=now_ist, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_ist)

    calories: Mapped[float] = mapped_column(Float, default=0)
    protein_g: Mapped[float] = mapped_column(Float, default=0)
    carbs_g: Mapped[float] = mapped_column(Float, default=0)
    fat_g: Mapped[float] = mapped_column(Float, default=0)
    fiber_g: Mapped[float] = mapped_column(Float, default=0)
    sugar_g: Mapped[float] = mapped_column(Float, default=0)
    sodium_mg: Mapped[float] = mapped_column(Float, default=0)

    user: Mapped["User"] = relationship(back_populates="meals")  # noqa: F821
    ingredients: Mapped[list["MealIngredient"]] = relationship(
        back_populates="meal",
        cascade="all, delete-orphan",
        order_by="MealIngredient.position",
    )


class MealIngredient(Base):
    __tablename__ = "meal_ingredients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    meal_id: Mapped[str] = mapped_column(String(36), ForeignKey("meals.id", ondelete="CASCADE"), index=True)

    position: Mapped[int] = mapped_column(Integer, default=0)
    name: Mapped[str] = mapped_column(String(255))
    weight_g: Mapped[float] = mapped_column(Float, default=0)
    unit: Mapped[str] = mapped_column(String(32), default="g")
    confidence: Mapped[float] = mapped_column(Float, default=0)

    calories: Mapped[float] = mapped_column(Float, default=0)
    protein_g: Mapped[float] = mapped_column(Float, default=0)
    carbs_g: Mapped[float] = mapped_column(Float, default=0)
    fat_g: Mapped[float] = mapped_column(Float, default=0)
    fiber_g: Mapped[float] = mapped_column(Float, default=0)
    sugar_g: Mapped[float] = mapped_column(Float, default=0)
    sodium_mg: Mapped[float] = mapped_column(Float, default=0)

    meal: Mapped["Meal"] = relationship(back_populates="ingredients")
