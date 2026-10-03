from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MealType = Literal["breakfast", "lunch", "dinner", "snack"]


class NutritionTotals(BaseModel):
    calories: float = 0
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0
    fiber_g: float = 0
    sugar_g: float = 0
    sodium_mg: float = 0


class IngredientIn(BaseModel):
    name: str
    weight_g: float = Field(ge=0)
    unit: str = "g"
    confidence: float = Field(default=1.0, ge=0, le=1)
    calories: float = 0
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0
    fiber_g: float = 0
    sugar_g: float = 0
    sodium_mg: float = 0


class IngredientOut(IngredientIn):
    model_config = ConfigDict(from_attributes=True)
    id: str
    position: int = 0


class AnalyzeMealResponse(BaseModel):
    meal_name: str
    meal_type: MealType
    image_url: str | None = None
    confidence: float
    engine: str = "AI"
    ingredients: list[IngredientIn]
    totals: NutritionTotals


class MealCreate(BaseModel):
    name: str
    meal_type: MealType = "lunch"
    image_url: str | None = None
    notes: str | None = None
    consumed_at: datetime | None = None
    ingredients: list[IngredientIn]


class MealUpdate(BaseModel):
    name: str | None = None
    meal_type: MealType | None = None
    notes: str | None = None
    consumed_at: datetime | None = None
    ingredients: list[IngredientIn] | None = None


class MealOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    meal_type: MealType
    image_url: str | None
    notes: str | None
    consumed_at: datetime
    created_at: datetime

    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    sugar_g: float
    sodium_mg: float

    ingredients: list[IngredientOut] = []
