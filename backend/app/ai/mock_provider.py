"""Default mock implementations of the AI pipeline.

The mock chooses a plausible Indian meal "template" (e.g. North-Indian thali,
South-Indian breakfast, biryani plate, ...) based on a stable hash of the image
bytes, so the same image returns the same result every time. Macros are
computed from the seeded Indian-foods nutrition database.

This is intentionally fast (no network, no model load) so the whole flow can
be exercised end-to-end during development and demos.
"""
from __future__ import annotations

import asyncio
import hashlib
import io
import random
from datetime import datetime

from app.ai.base import (
    DetectedIngredient,
    EstimatedIngredient,
    MealAnalysis,
    NutritionEnrichedIngredient,
    VisionLabel,
    VisionResult,
)
from app.data.indian_foods import default_serving, macros_for
from app.utils import now_ist

# Each template is a meal name + list of (food alias, portion multiplier).
_TEMPLATES: list[tuple[str, str, list[tuple[str, float]]]] = [
    # (meal_name, meal_type, [(ingredient, portion_multiplier_vs_default)])
    ("North Indian Thali",          "lunch",     [("roti", 2), ("dal tadka", 1), ("paneer", 0.8), ("rice", 0.8), ("salad", 0.5), ("curd", 0.6)]),
    ("South Indian Breakfast",      "breakfast", [("idli", 3), ("sambar", 1), ("coconut chutney", 1)]),
    ("Masala Dosa Plate",           "breakfast", [("masala dosa", 1), ("sambar", 0.8), ("coconut chutney", 1)]),
    ("Poha Plate",                  "breakfast", [("poha", 1), ("chai", 1)]),
    ("Upma Bowl",                   "breakfast", [("upma", 1), ("coconut chutney", 0.5)]),
    ("Chole Bhature",               "lunch",     [("chole", 1), ("paratha", 1.2), ("salad", 0.6)]),
    ("Rajma Chawal",                "lunch",     [("rajma", 1), ("rice", 1.1)]),
    ("Dal Chawal Bowl",             "lunch",     [("dal tadka", 1), ("rice", 1.1), ("pickle", 0.5)]),
    ("Paneer Butter Masala Combo",  "dinner",    [("paneer butter masala", 1), ("naan", 1), ("salad", 0.5)]),
    ("Chicken Biryani Plate",       "dinner",    [("chicken biryani", 1.2), ("raita", 1)]),
    ("Veg Biryani Plate",           "dinner",    [("veg biryani", 1.2), ("raita", 1)]),
    ("Khichdi Bowl",                "dinner",    [("khichdi", 1.1), ("curd", 0.8), ("pickle", 0.5)]),
    ("Pav Bhaji",                   "snack",     [("pav bhaji", 1)]),
    ("Vada Pav Snack",              "snack",     [("vada pav", 1), ("chai", 1)]),
    ("Samosa Snack",                "snack",     [("samosa", 2), ("green chutney", 1)]),
    ("Egg & Toast",                 "breakfast", [("boiled egg", 2), ("bread", 2), ("banana", 1)]),
    ("Grilled Chicken Bowl",        "lunch",     [("grilled chicken", 1.2), ("brown rice", 0.8), ("mixed salad", 1)]),
    ("Palak Paneer Combo",          "dinner",    [("palak paneer", 1), ("roti", 2), ("rice", 0.6)]),
    ("Aloo Paratha Breakfast",      "breakfast", [("aloo paratha", 2), ("curd", 1), ("pickle", 0.5)]),
    ("Fish Curry Meal",             "dinner",    [("fish curry", 1), ("rice", 1.0), ("salad", 0.5)]),
]

_CAPTIONS = [
    "A photo of a freshly served Indian meal with multiple components.",
    "Plated Indian food with rice, curry and side dishes.",
    "Close-up of a home-cooked Indian thali.",
    "Steaming hot Indian breakfast with chutneys.",
    "Indian street-food snack on a plate.",
]


def _pick_template(image_bytes: bytes) -> tuple[str, str, list[tuple[str, float]]]:
    digest = hashlib.sha256(image_bytes or b"empty").digest()
    idx = int.from_bytes(digest[:4], "big") % len(_TEMPLATES)
    return _TEMPLATES[idx]


def _seeded_rng(image_bytes: bytes) -> random.Random:
    digest = hashlib.sha256(image_bytes or b"empty").digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def _meal_type_for_now() -> str:
    hour = now_ist().hour
    if 4 <= hour < 11:
        return "breakfast"
    if 11 <= hour < 16:
        return "lunch"
    if 16 <= hour < 19:
        return "snack"
    return "dinner"


def _round(v: float, ndigits: int = 1) -> float:
    return round(v, ndigits)


class _MockVisionService:
    async def describe(self, image_bytes: bytes) -> VisionResult:
        await asyncio.sleep(0.15)
        rng = _seeded_rng(image_bytes)
        return VisionResult(
            caption=rng.choice(_CAPTIONS),
            labels=[
                VisionLabel(label="food", score=0.98),
                VisionLabel(label="plate", score=0.93),
                VisionLabel(label="curry", score=0.81),
            ],
        )


class _MockIngredientExtractor:
    def __init__(self, template):
        self._template = template

    async def extract(self, vision: VisionResult) -> list[DetectedIngredient]:
        await asyncio.sleep(0.2)
        out: list[DetectedIngredient] = []
        for name, _ in self._template[2]:
            out.append(DetectedIngredient(name=name, confidence=round(random.uniform(0.86, 0.99), 2)))
        return out


class _MockPortionEstimator:
    def __init__(self, template, rng: random.Random):
        self._template = template
        self._rng = rng

    async def estimate(
        self,
        ingredients: list[DetectedIngredient],
        image_bytes: bytes | None = None,
    ) -> list[EstimatedIngredient]:
        await asyncio.sleep(0.2)
        multipliers = {n: m for n, m in self._template[2]}
        out: list[EstimatedIngredient] = []
        for ing in ingredients:
            mult = multipliers.get(ing.name, 1.0)
            serving = default_serving(ing.name)
            if serving is None:
                weight, unit = 100.0, "g"
            else:
                weight, unit = serving
            jitter = self._rng.uniform(0.9, 1.1)
            out.append(
                EstimatedIngredient(
                    name=ing.name,
                    weight_g=_round(weight * mult * jitter, 1),
                    unit=unit,
                    confidence=ing.confidence,
                )
            )
        return out


class _MockNutritionService:
    def enrich(self, ingredients: list[EstimatedIngredient]) -> list[NutritionEnrichedIngredient]:
        enriched: list[NutritionEnrichedIngredient] = []
        for ing in ingredients:
            macros = macros_for(ing.name, ing.weight_g) or {
                "calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0,
                "fiber_g": 0, "sugar_g": 0, "sodium_mg": 0,
            }
            display_name = ing.name.title() if ing.name.islower() else ing.name
            enriched.append(
                NutritionEnrichedIngredient(
                    name=display_name,
                    weight_g=ing.weight_g,
                    unit=ing.unit,
                    confidence=ing.confidence,
                    **macros,
                )
            )
        return enriched


def _image_size(image_bytes: bytes) -> tuple[int | None, int | None]:
    if not image_bytes:
        return None, None
    try:
        from PIL import Image  # local import so PIL is optional at import-time
        with Image.open(io.BytesIO(image_bytes)) as im:
            return im.width, im.height
    except Exception:
        return None, None


class MockMealAnalyzer:
    """End-to-end mock that composes the four pipeline stages above."""

    engine_label = "Demo mode"

    async def analyze(self, image_bytes: bytes, *, filename: str | None = None) -> MealAnalysis:
        template = _pick_template(image_bytes)
        meal_name, meal_type_default, _ = template
        rng = _seeded_rng(image_bytes)

        vision_svc = _MockVisionService()
        ing_svc = _MockIngredientExtractor(template)
        portion_svc = _MockPortionEstimator(template, rng)
        nutrition_svc = _MockNutritionService()

        vision = await vision_svc.describe(image_bytes)
        vision.width, vision.height = _image_size(image_bytes)
        detected = await ing_svc.extract(vision)
        estimated = await portion_svc.estimate(detected, image_bytes)
        enriched = nutrition_svc.enrich(estimated)

        # Prefer the template's meal-type, but at least respect current time when generic.
        meal_type = meal_type_default or _meal_type_for_now()
        confidence = round(sum(i.confidence for i in enriched) / max(len(enriched), 1), 2)

        return MealAnalysis(
            meal_name=meal_name,
            meal_type=meal_type,
            confidence=confidence,
            ingredients=enriched,
        )
