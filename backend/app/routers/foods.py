from typing import Any

from fastapi import APIRouter

from app.data.indian_foods import all_foods

router = APIRouter(prefix="/api/foods", tags=["foods"])


@router.get("")
async def list_foods() -> dict[str, Any]:
    """Return the local Indian foods catalog so the frontend can offer an
    autocomplete picker for manual meal entry.

    Per-100g macros are included so the client can compute portion-scaled
    macros locally without a round-trip when the user picks a food.
    """
    items = []
    for f in all_foods():
        items.append({
            "name": f.name,
            "aliases": list(f.aliases),
            "default_weight_g": f.default_weight_g,
            "default_unit": f.default_unit,
            "per_100g": {
                "calories":  f.kcal,
                "protein_g": f.protein_g,
                "carbs_g":   f.carbs_g,
                "fat_g":     f.fat_g,
                "fiber_g":   f.fiber_g,
                "sugar_g":   f.sugar_g,
                "sodium_mg": f.sodium_mg,
            },
        })
    return {"items": items}
