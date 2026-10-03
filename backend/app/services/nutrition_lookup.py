"""Combined nutrition source.

Lookup order:
    1. Local Indian-foods table (curated, ~120 entries from IFCT-style data).
    2. USDA FoodData Central — real free public API, requires an API key
       (sign up at https://fdc.nal.usda.gov/api-key-signup).

The local table is fast and authoritative for Indian dishes that the USDA
database doesn't model well (e.g. "Dal tadka", "Masala dosa"). USDA covers
the long tail of raw ingredients and Western foods that an LLM may detect.

Set `USDA_API_KEY` in your environment to enable the fallback. Without it,
unknown items will return zeros (which is what the mock provider has always
done).
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import get_settings
from app.data.indian_foods import macros_for as local_macros_for

log = logging.getLogger(__name__)

USDA_SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

# USDA nutrient IDs we care about.
_USDA_NUTRIENT_MAP = {
    1008: "calories",   # Energy (kcal)
    1003: "protein_g",  # Protein
    1004: "fat_g",      # Total lipid (fat)
    1005: "carbs_g",    # Carbohydrate, by difference
    1079: "fiber_g",    # Fiber, total dietary
    2000: "sugar_g",    # Sugars, total
    1093: "sodium_mg",  # Sodium, Na
}

_EMPTY = {k: 0.0 for k in ("calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "sugar_g", "sodium_mg")}


class NutritionLookup:
    def __init__(self) -> None:
        s = get_settings()
        self._usda_key = s.usda_api_key
        self._timeout = httpx.Timeout(8.0, connect=4.0)
        # USDA's edge rejects the default python-httpx UA with HTTP 400.
        self._headers = {"User-Agent": "NutriAI/0.1 (+https://github.com/nutriai)", "Accept": "application/json"}

    async def lookup(self, name: str, weight_g: float) -> dict[str, float]:
        """Return per-portion macros for `name` at `weight_g`. Always returns
        the seven-key dict, with zeros if nothing was found."""
        local = local_macros_for(name, weight_g)
        if local and local.get("calories", 0) > 0:
            return local

        if self._usda_key:
            usda = await self._usda(name, weight_g)
            if usda:
                return usda

        return local if local is not None else dict(_EMPTY)

    async def _usda(self, name: str, weight_g: float) -> dict[str, float] | None:
        base_params: dict[str, object] = {
            "query": name,
            "api_key": self._usda_key,
            # Fetch a few candidates so we can prefer the most canonical entry
            # (USDA sorts by relevance but the first hit is often a Branded
            # restaurant item that's calorie-inflated vs. the raw food).
            "pageSize": 5,
        }
        # Try curated datasets first; USDA's edge sporadically rejects the
        # dataType filter with HTTP 400, so fall back to an unfiltered search
        # which is much more lenient.
        attempts: list[dict[str, object]] = [
            {**base_params, "dataType": ["Foundation", "SR Legacy", "Survey (FNDDS)"]},
            base_params,
        ]
        data: dict[str, Any] | None = None
        async with httpx.AsyncClient(timeout=self._timeout, headers=self._headers) as client:
            for params in attempts:
                try:
                    resp = await client.get(USDA_SEARCH_URL, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        break
                    if 400 <= resp.status_code < 500:
                        continue  # try next attempt
                    resp.raise_for_status()
                except Exception as exc:
                    log.warning("USDA lookup error for %r: %s", name, exc)
                    continue
        if data is None:
            return None

        foods = data.get("foods") or []
        if not foods:
            return None
        food = _pick_best_usda_food(name, foods)

        per100: dict[str, float] = {}
        for n in food.get("foodNutrients") or []:
            nid = n.get("nutrientId")
            val = n.get("value")
            if nid in _USDA_NUTRIENT_MAP and val is not None:
                per100[_USDA_NUTRIENT_MAP[nid]] = float(val)
        if not per100.get("calories"):
            return None

        factor = weight_g / 100.0
        return {key: round(per100.get(key, 0) * factor, 1) for key in _EMPTY.keys()}


def _pick_best_usda_food(query: str, foods: list[dict[str, Any]]) -> dict[str, Any]:
    """Choose the most generic / canonical entry among USDA candidates.

    USDA's relevance ranker often surfaces Branded restaurant items first; for
    a query like "Eggplant" the top hit may be "Eggplant Parmesan, frozen"
    rather than raw eggplant. Prefer (in order): an exact case-insensitive
    description match, a description starting with the query, a Foundation /
    SR Legacy entry, then the shortest description (= simplest entry).
    """
    q = query.strip().lower()

    def score(food: dict[str, Any]) -> tuple[int, int, int]:
        desc = str(food.get("description") or "").strip().lower()
        dtype = str(food.get("dataType") or "")
        exact = 0 if desc == q else 1
        starts = 0 if desc.startswith(q) else 1
        # Lower dataType rank = better source. Foundation/SR Legacy beat Branded.
        dtype_rank = {"Foundation": 0, "SR Legacy": 1, "Survey (FNDDS)": 2}.get(dtype, 3)
        # Tie-break: shorter description = more generic.
        return (exact, starts, dtype_rank * 1000 + len(desc))

    return min(foods, key=score)


_lookup: NutritionLookup | None = None


def get_nutrition_lookup() -> NutritionLookup:
    global _lookup
    if _lookup is None:
        _lookup = NutritionLookup()
    return _lookup
