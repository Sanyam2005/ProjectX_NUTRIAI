"""Interfaces for the AI pipeline.

Each protocol corresponds to one swappable stage:

    image bytes
      │
      ▼  VisionService.describe()
    VisionResult (labels, regions, raw caption)
      │
      ▼  IngredientExtractor.extract()
    DetectedIngredient[]
      │
      ▼  PortionEstimator.estimate()
    EstimatedIngredient[]   (weight + unit)
      │
      ▼  NutritionService.enrich()
    NutritionEnrichedIngredient[]   (calories + macros)
      │
      ▼  MealAnalyzer.analyze()  (composes the above)
    MealAnalysis

Real providers (Qwen2.5-VL, YOLOv8, SAM, Florence-2, SmolVLM, ...) implement
these protocols. The mock provider in `app.ai.mock_provider` implements
MealAnalyzer end-to-end without external dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol


@dataclass(slots=True)
class BoundingBox:
    x: float
    y: float
    w: float
    h: float


@dataclass(slots=True)
class VisionLabel:
    label: str
    score: float
    box: BoundingBox | None = None


@dataclass(slots=True)
class VisionResult:
    caption: str
    labels: list[VisionLabel] = field(default_factory=list)
    width: int | None = None
    height: int | None = None


@dataclass(slots=True)
class DetectedIngredient:
    name: str
    confidence: float


@dataclass(slots=True)
class EstimatedIngredient:
    name: str
    weight_g: float
    unit: str
    confidence: float


@dataclass(slots=True)
class NutritionEnrichedIngredient:
    name: str
    weight_g: float
    unit: str
    confidence: float
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    sugar_g: float
    sodium_mg: float


MealType = Literal["breakfast", "lunch", "dinner", "snack"]


@dataclass(slots=True)
class MealAnalysis:
    meal_name: str
    meal_type: MealType
    confidence: float
    ingredients: list[NutritionEnrichedIngredient]

    @property
    def totals(self) -> dict[str, float]:
        keys = ("calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "sugar_g", "sodium_mg")
        return {k: round(sum(getattr(i, k) for i in self.ingredients), 1) for k in keys}


# ---------------------------------------------------------------------------
# Protocols
# ---------------------------------------------------------------------------


class VisionService(Protocol):
    async def describe(self, image_bytes: bytes) -> VisionResult: ...


class IngredientExtractor(Protocol):
    async def extract(self, vision: VisionResult) -> list[DetectedIngredient]: ...


class PortionEstimator(Protocol):
    async def estimate(
        self,
        ingredients: list[DetectedIngredient],
        image_bytes: bytes | None = None,
    ) -> list[EstimatedIngredient]: ...


class NutritionService(Protocol):
    def enrich(self, ingredients: list[EstimatedIngredient]) -> list[NutritionEnrichedIngredient]: ...


class MealAnalyzer(Protocol):
    async def analyze(self, image_bytes: bytes, *, filename: str | None = None) -> MealAnalysis: ...


class RecommendationEngine(Protocol):
    async def recommend(self, user_id: str, *, recent_calories: float, goal_calories: float) -> list[str]: ...
