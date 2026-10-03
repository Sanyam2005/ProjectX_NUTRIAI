"""Open Food Facts client — branded / packaged food lookup.

The model is good at identifying packaged products (KitKat, Maggi, Lay's, etc.)
but its training-time macro recall isn't always tight for specific SKUs. Open
Food Facts hosts crowdsourced label values for 3M+ products and is free with
no API key, so we use it as a second-pass override whenever an ingredient
name looks branded.

The lookup is best-effort: a network failure or empty result just falls back
to whatever the model (or USDA / local table) returned.
"""
from __future__ import annotations

import logging
import re
from typing import Any

import httpx

log = logging.getLogger(__name__)

# The legacy CGI endpoint actually honours `search_terms` and is far more
# stable than the v2 /api/v2/search API which often 503s and ignores the
# query for free-text lookups.
OFF_SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"

# OFF requires a real-looking User-Agent; default httpx UA gets throttled.
_OFF_HEADERS = {
    "User-Agent": "NutriAI/0.1 (+https://github.com/nutriai)",
    "Accept": "application/json",
}

_OFF_TIMEOUT = httpx.Timeout(4.0, connect=2.0)

# Brand keywords we want to definitely route through OFF. Lowercase, substring
# match. The middle-cap regex below catches "KitKat", "McDonald", "iPhone"-style
# patterns even when they're not in this list.
_BRAND_WORDS: frozenset[str] = frozenset({
    "kitkat", "kit kat", "kit-kat", "snickers", "twix", "mars", "milky way",
    "dairy milk", "cadbury", "5 star", "munch", "perk", "gems",
    "oreo", "bourbon", "good day", "parle-g", "parle g", "marie",
    "lays", "lay's", "kurkure", "bingo", "doritos", "pringles", "uncle chipps",
    "coca-cola", "coca cola", "coke", "pepsi", "sprite", "fanta", "thums up",
    "red bull", "monster", "yakult", "amul",
    "maggi", "knorr", "yippee", "wai wai", "top ramen", "patanjali",
    "britannia", "tiger biscuits", "mcvities",
    "nutella", "hershey", "ferrero", "rocher", "toblerone",
    "starbucks", "frappuccino", "monster energy",
    "haldiram", "bikaji", "lehar",
})

_MID_CAP_RE = re.compile(r"[a-z][A-Z]")


def looks_branded(name: str) -> bool:
    """Quick, conservative heuristic — does this ingredient name look like a
    branded packaged food? We want to avoid wasting OFF calls on generics
    like "dal" or "paneer butter masala"."""
    low = name.lower().strip()
    if any(b in low for b in _BRAND_WORDS):
        return True
    if _MID_CAP_RE.search(name):
        return True
    if "&" in name or "®" in name or "™" in name or "'s " in low:
        return True
    return False


def _pick_per100(nutriments: dict[str, Any], *keys: str) -> float | None:
    for k in keys:
        v = nutriments.get(k)
        if v is None:
            continue
        try:
            return float(v)
        except (TypeError, ValueError):
            continue
    return None


async def lookup_branded(name: str, weight_g: float) -> dict[str, float] | None:
    """Look the product up on Open Food Facts and return macros scaled to
    ``weight_g``. Returns ``None`` if there's no usable match.
    """
    if weight_g <= 0:
        return None

    params: dict[str, Any] = {
        "search_terms": name,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "fields": "product_name,brands,quantity,serving_size,nutriments",
        # Pull a handful of candidates so we can pick the cleanest match
        # ourselves — OFF's own sort orders surface odd variants first.
        "page_size": 8,
    }
    # OFF occasionally throws 5xx for a few seconds at a time. One quick
    # retry absorbs those without making the user wait long.
    data: dict[str, Any] | None = None
    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=_OFF_TIMEOUT, headers=_OFF_HEADERS) as client:
                resp = await client.get(OFF_SEARCH_URL, params=params)
            if resp.status_code == 200:
                data = resp.json()
                break
            if resp.status_code < 500:
                return None  # 4xx isn't worth retrying
        except Exception as exc:
            log.warning("OFF lookup attempt %d failed for %r: %s", attempt + 1, name, exc)
    if data is None:
        return None

    products = data.get("products") or []
    if not products:
        return None

    best = _pick_best_product(products, name)
    if best is None:
        return None
    n = best.get("nutriments") or {}

    kcal_100 = _pick_per100(n, "energy-kcal_100g", "energy_kcal_100g")
    if not kcal_100 or kcal_100 <= 0:
        # Some products only carry kJ. Convert kJ → kcal.
        kj_100 = _pick_per100(n, "energy_100g", "energy-kj_100g")
        if kj_100 and kj_100 > 0:
            kcal_100 = kj_100 / 4.184
    if not kcal_100 or kcal_100 <= 0:
        return None

    protein_100 = _pick_per100(n, "proteins_100g") or 0.0
    carbs_100   = _pick_per100(n, "carbohydrates_100g") or 0.0
    fat_100     = _pick_per100(n, "fat_100g") or 0.0
    fiber_100   = _pick_per100(n, "fiber_100g") or 0.0
    sugar_100   = _pick_per100(n, "sugars_100g") or 0.0
    # OFF stores sodium in grams per 100 g; we want milligrams.
    sodium_g_100 = _pick_per100(n, "sodium_100g") or 0.0
    sodium_mg_100 = sodium_g_100 * 1000.0

    factor = weight_g / 100.0
    return {
        "calories":  round(kcal_100   * factor, 1),
        "protein_g": round(protein_100 * factor, 1),
        "carbs_g":   round(carbs_100  * factor, 1),
        "fat_g":     round(fat_100    * factor, 1),
        "fiber_g":   round(fiber_100  * factor, 1),
        "sugar_g":   round(sugar_100  * factor, 1),
        "sodium_mg": round(sodium_mg_100 * factor, 1),
    }


_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def _norm(s: str) -> str:
    return _ALNUM_RE.sub("", (s or "").lower())


def _pick_best_product(products: list[dict[str, Any]], query: str) -> dict[str, Any] | None:
    """Choose the cleanest product among OFF candidates.

    Sort key (lower is better):
      1. Whose normalised name equals the normalised query (exact match wins).
      2. Whose normalised name *starts* with the query (canonical variant).
      3. Has full kcal + P/C/F nutrition (drops sauce-only / water entries).
      4. Shorter product names beat longer ones (= more generic SKU).
    """
    q = _norm(query)

    def has_full_macros(p: dict[str, Any]) -> bool:
        n = p.get("nutriments") or {}
        kcal = _pick_per100(n, "energy-kcal_100g", "energy_kcal_100g", "energy_100g")
        return bool(kcal and kcal > 0
                    and _pick_per100(n, "carbohydrates_100g") is not None
                    and _pick_per100(n, "fat_100g") is not None)

    def score(p: dict[str, Any]) -> tuple[int, int, int, int]:
        name_norm = _norm(p.get("product_name") or "")
        exact = 0 if name_norm == q else 1
        starts = 0 if name_norm.startswith(q) else 1
        complete = 0 if has_full_macros(p) else 1
        # Shorter normalised name = more generic ("Kitkat" beats "Kitkat win gold")
        return (exact, starts, complete, len(name_norm))

    candidates = [p for p in products if (p.get("nutriments") or {})]
    if not candidates:
        return None
    return min(candidates, key=score)
