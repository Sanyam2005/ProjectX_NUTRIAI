from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Gender = Literal["male", "female", "other"]
ActivityLevel = Literal["sedentary", "light", "moderate", "active", "very_active"]


class GoalIn(BaseModel):
    weight_kg: float | None = Field(default=None, ge=0)
    target_weight_kg: float | None = Field(default=None, ge=0)
    height_cm: float | None = Field(default=None, ge=0)
    age: int | None = Field(default=None, ge=0)
    gender: Gender | None = None
    activity_level: ActivityLevel = "moderate"

    target_calories: int = Field(default=2000, ge=500, le=10000)
    target_protein_g: int = Field(default=80, ge=0)
    target_carbs_g: int = Field(default=250, ge=0)
    target_fat_g: int = Field(default=65, ge=0)
    target_fiber_g: int = Field(default=30, ge=0)
    target_water_ml: int = Field(default=2500, ge=0)


class GoalOut(GoalIn):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    updated_at: datetime
