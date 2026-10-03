"""Real vision-based meal analyzer powered by GitHub Models.

Uses an OpenAI-compatible chat-completions endpoint (default
https://models.github.ai/inference) and any vision-capable model the caller
has access to under their GitHub PAT — gpt-4o, gpt-4o-mini,
Llama-3.2-90B-Vision-Instruct, Phi-3.5-vision-instruct, etc.

The model is prompted to return strict JSON describing the meal. We then
resolve calories/macros for each detected ingredient using
`NutritionLookup` (local Indian table → USDA fallback).
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import re
from typing import Any, cast

import httpx

from app.ai.base import MealAnalysis, MealType, NutritionEnrichedIngredient
from app.data.indian_foods import default_serving
from app.services.nutrition_lookup import NutritionLookup
from app.services.open_food_facts import lookup_branded, looks_branded

log = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are NutriAI, a computer-vision system that identifies meals from ANY cuisine and estimates portion sizes.

You will receive ONE image of a meal. Identify every distinct food component on the plate and estimate its serving size. Treat Indian, Middle-Eastern, Mediterranean, East Asian, South-East Asian, European, Latin American, African, and North American foods with equal care — never bias your guess toward one cuisine.

Output rules:
- Return STRICT JSON only. No prose, no markdown, no code fences.
- Use the most specific, widely-recognised English name for each item. Examples (NOT exhaustive — use whatever fits the image best):
  * Indian: Dal tadka, Paneer butter masala, Roti, Masala dosa, Idli, Sambar, Biryani, Raita, Chole, Aloo gobi, Samosa, Gulab jamun, Masala chai.
  * Middle-Eastern / Mediterranean: Hummus, Baba ganoush, Falafel, Tabbouleh, Pita bread, Olives, Feta cheese, Tzatziki, Shawarma, Kebab, Grilled halloumi, Greek salad.
  * East Asian: Steamed rice, Fried rice, Sushi, Ramen, Miso soup, Edamame, Tempura, Pad thai, Pho, Spring roll, Dim sum, Mapo tofu.
  * European / American: Pizza, Pasta, Spaghetti bolognese, Caesar salad, Burger, French fries, Croissant, Omelette, Pancakes, Scrambled eggs, Bacon, Sausage, Grilled chicken, Steak.
  * Latin: Tacos, Burrito, Guacamole, Black beans, Rice and beans, Empanadas, Quesadilla.
  * Whole foods: Banana, Apple, Orange, Avocado, Cucumber, Tomato, Carrot, Lettuce, Spinach, Boiled egg, Grilled fish, Mixed nuts, Yogurt.

- Pick the SINGLE clearest name per item; do not stack synonyms like "hummus / chickpea dip".
- DISAMBIGUATION: when several named dishes share the same sauce / gravy / dough / batter but differ only by the visible solid component, name the dish after that solid component, not the sauce. Examples: if you see paneer cubes in an orange tomato-cream gravy, it is "Paneer butter masala", not "Butter chicken"; chicken pieces in the same gravy → "Butter chicken"; lamb pieces → "Lamb curry / Rogan josh"; cubed cottage cheese in spinach gravy → "Palak paneer", not "Palak chicken". The same idea applies outside India: visible solid components win over visible sauce color.
- Pick a portion unit that fits the dish (g, piece, bowl, cup, ml, slice, tbsp).
- Reference portions when in doubt:
  * 1 cup cooked rice / pasta = 180 g    * 1 slice bread = 30 g
  * 1 roti / tortilla / pita  = 40 g     * 1 medium piece naan / flatbread = 80 g
  * 1 bowl curry / dal / soup = 150 g    * 1 bowl rice / noodles = 250 g
  * 1 medium falafel = 18 g              * 1 tbsp hummus / dip = 15 g
  * 1 medium olive = 4 g                 * 1 slice cheese = 25 g
  * 1 boiled egg = 50 g                  * 1 chicken thigh = 80 g
  * 1 medium banana = 120 g              * 1 medium apple = 180 g
  * 1 slice pizza = 100 g                * 1 burger patty = 110 g

Schema (return EXACTLY this shape):
{
  "meal_name": "short, descriptive (e.g. 'Mediterranean Mezze Plate', 'Masala Dosa Plate', 'Margherita Pizza')",
  "meal_type": "breakfast" | "lunch" | "dinner" | "snack",
  "confidence": 0.0..1.0,
  "ingredients": [
    {
      "name":      "string",
      "weight_g":  number,
      "unit":      "g" | "piece" | "bowl" | "cup" | "ml" | "slice" | "tbsp",
      "calories":  number,   // total kcal for THIS exact weight_g, not per-100g
      "protein_g": number,   // total grams of protein for this portion
      "carbs_g":   number,   // total grams of carbs for this portion
      "fat_g":     number    // total grams of fat for this portion
    }
  ]
}

Keep each ingredient object compact (the four fields above are mandatory — nothing else). Do NOT include fiber, sugar, sodium, or per-ingredient confidence; the app fills those in.

NUTRITION ANCHORS (USDA-style, per 100 g). Use as your baseline and scale to weight_g; the FULL plate's calories must agree with 4·protein_g + 4·carbs_g + 9·fat_g within 15%:
  * Raw vegetables (eggplant, spinach, lettuce, tomato, cucumber): 15–30 kcal/100g, ≤1 P, ≤6 C, ≤0.5 F
  * Cooked rice / cooked pasta / cooked noodles: 130–170 kcal/100g, 3 P, 30 C, 0.5–3 F
  * Bread / roti / naan / kulcha / tortilla / pizza crust: 250–290 kcal/100g, 9 P, 50 C, 4–5 F
  * Indian curries (dal, sambar, butter chicken, paneer butter masala, palak paneer): 130–230 kcal/100g, 6–13 P, 6–12 C, 5–18 F
  * Cheese (cheddar/mozzarella/feta/paneer): 260–400 kcal/100g, 14–25 P, ≤4 C, 20–33 F
  * Lean meat / fish / shrimp, cooked: 130–180 kcal/100g, 22–31 P, ≤2 C, 3–8 F
  * Fatty cuts / bacon / sausage: 300–540 kcal/100g, 12–37 P, ≤2 C, 25–45 F
  * Whole egg (1 = 50 g = 78 kcal): 155 kcal/100g, 13 P, 1 C, 11 F
  * Banana: 89 kcal/100g (1 medium ≈ 107 kcal)
  * Avocado / hummus / olives: 115–170 kcal/100g, 0.8–8 P, 6–14 C, 10–15 F
  * Oil / butter / mayo: 680–900 kcal/100g, ≤1 P, ≤1 C, 75–100 F
  * Sushi (rice + fish nigiri, per piece ≈ 40 g): 50 kcal, 3 P, 8 C, 0.5 F

NEVER invent extreme values. Raw vegetables stay <50 kcal/100g (200 g eggplant ≤ 60 kcal, ≤ 2 g protein — do NOT bump protein up because the dish is "stir-fried"; the oil counts as a separate ingredient).

PACKAGED / BRANDED FOODS — IMPORTANT:
- If the image shows a packaged product with a visible Nutrition Facts panel, READ THE LABEL. The per-serving values printed on the package are authoritative; use them and set weight_g to the printed serving size (or the visible piece weight). Do NOT fall back to generic anchors when the label is legible.
- If you can identify a specific brand by its wrapper / logo (KitKat, Dairy Milk, Snickers, Twix, Oreo, Maggi, Lay's, Doritos, Coca-Cola, Pepsi, Sprite, Red Bull, Yakult, Britannia biscuits, Parle-G, etc.) but the back label isn't visible, use the standard label values for that product. Reference per 100 g (or per serving where noted):
  * Milk chocolate wafer bar (KitKat 4-finger 41.5 g = 215 kcal, Dairy Milk 50 g = 270 kcal): ~520 kcal, 7 P, 60 C (~50 sugar), 28 F per 100 g
  * Filled chocolate (Snickers, Twix, Mars): ~490 kcal, 8 P, 60 C, 24 F per 100 g
  * Plain dark chocolate (70%+): ~580 kcal, 8 P, 38 C, 42 F per 100 g
  * Sandwich cookies (Oreo, Bourbon): ~480 kcal, 5 P, 70 C, 20 F per 100 g
  * Glucose / digestive biscuits: ~450 kcal, 7 P, 70 C, 14 F per 100 g
  * Potato chips / Lay's / Kurkure: ~540 kcal, 6 P, 55 C, 32 F per 100 g
  * Cola / sweet soda: ~42 kcal/100 ml (1 can 330 ml = 140 kcal, 35 g sugar)
  * Diet soda: ~0 kcal
  * Energy drink (Red Bull 250 ml): 110 kcal, 27 g sugar
  * Maggi / instant noodles (1 packet ~70 g): ~310 kcal, 7 P, 40 C, 13 F
  * Plain chips packet (small ~30 g): ~160 kcal, 2 P, 16 C, 10 F
- Always set weight_g to the ACTUAL piece in the photo (a 4-finger KitKat is 41.5 g, a 2-finger is 21 g, a 50 g Dairy Milk is 50 g). When the visible piece is partial, scale.

If you genuinely cannot see any food, return ingredients = []."""


USER_TEXT = "Analyze this meal photo and return the JSON described in the system prompt."


def _detect_content_type(image_bytes: bytes, filename: str | None) -> str:
    head = image_bytes[:12]
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if head[8:12] == b"WEBP":
        return "image/webp"
    if filename and "." in filename:
        ext = filename.rsplit(".", 1)[-1].lower()
        return {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(
            ext, "image/jpeg"
        )
    return "image/jpeg"


def _parse_json(content: str) -> dict[str, Any]:
    try:
        return cast(dict[str, Any], json.loads(content))
    except json.JSONDecodeError:
        # Salvage a JSON object embedded in markdown / prose.
        match = re.search(r"\{[\s\S]*\}", content)
        if not match:
            raise
        return cast(dict[str, Any], json.loads(match.group(0)))


def _coerce_meal_type(value: Any) -> MealType:
    if isinstance(value, str) and value.lower() in ("breakfast", "lunch", "dinner", "snack"):
        return cast(MealType, value.lower())
    return "lunch"


_MACRO_KEYS = ("calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "sugar_g", "sodium_mg")


def _macros_from_ai(raw: dict[str, Any]) -> dict[str, float] | None:
    """Pull macro estimates out of the model's per-ingredient JSON.

    Returns ``None`` if the model didn't include kcal/macros; otherwise a dict
    with all seven keys (missing ones become zero, which is fine for sums).
    """
    if "calories" not in raw and "kcal" not in raw:
        return None
    out: dict[str, float] = {}
    for k in _MACRO_KEYS:
        v = raw.get(k)
        if v is None and k == "calories":
            v = raw.get("kcal")
        try:
            out[k] = max(0.0, float(v)) if v is not None else 0.0
        except (TypeError, ValueError):
            out[k] = 0.0
    return out


class GitHubModelsMealAnalyzer:
    """End-to-end MealAnalyzer using GitHub Models for vision."""

    def __init__(
        self,
        *,
        token: str,
        model: str = "gpt-4o",
        endpoint: str = "https://models.github.ai/inference",
        lookup: NutritionLookup | None = None,
    ) -> None:
        if not token:
            raise ValueError("github_token is required for GitHubModelsMealAnalyzer")
        self._token = token
        self._model = model
        self._endpoint = endpoint.rstrip("/")
        self._lookup = lookup or NutritionLookup()
        self._timeout = httpx.Timeout(60.0, connect=10.0)

    @property
    def engine_label(self) -> str:
        return self._model

    async def analyze(self, image_bytes: bytes, *, filename: str | None = None) -> MealAnalysis:
        content_type = _detect_content_type(image_bytes, filename)
        data_url = f"data:{content_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"

        payload: dict[str, Any] = {
            "model": self._model,
            "temperature": 0.2,
            "max_tokens": 900,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": USER_TEXT},
                        {"type": "image_url", "image_url": {"url": data_url, "detail": "high"}},
                    ],
                },
            ],
        }

        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(f"{self._endpoint}/chat/completions", headers=headers, json=payload)
            if resp.status_code >= 400:
                log.error("GitHub Models error %s: %s", resp.status_code, resp.text[:1000])
                resp.raise_for_status()
            body = resp.json()

        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Unexpected response from GitHub Models: {body!r}") from exc

        parsed = _parse_json(content if isinstance(content, str) else json.dumps(content))

        meal_name = str(parsed.get("meal_name") or "Meal").strip() or "Meal"
        meal_type = _coerce_meal_type(parsed.get("meal_type"))
        overall_conf = float(parsed.get("confidence") or 0.85)

        raw_ingredients = parsed.get("ingredients") or []
        if not isinstance(raw_ingredients, list):
            raw_ingredients = []

        # Resolve nutrition. Preference order:
        #   1. Local Indian-foods table when it has a strong hit (deterministic anchor).
        #   2. The AI's own macro estimates if it provided sensible numbers in the
        #      response (no extra HTTP call, fastest path — typical case).
        #   3. USDA fallback (HTTP) for items the model didn't price.
        async def resolve(raw: dict[str, Any]) -> NutritionEnrichedIngredient | None:
            name = str(raw.get("name") or "").strip()
            if not name:
                return None
            weight_g = float(raw.get("weight_g") or 0)
            unit = str(raw.get("unit") or "g")
            confidence = float(raw.get("confidence") or overall_conf)

            if weight_g <= 0:
                ds = default_serving(name)
                if ds is not None:
                    weight_g, unit = ds
                else:
                    weight_g = 100.0

            macros = _macros_from_ai(raw)
            if macros is None or macros.get("calories", 0.0) <= 0:
                # Try local Indian table next; if that's also empty, fall back to USDA.
                macros = await self._lookup.lookup(name, weight_g)

            # For branded / packaged products (KitKat, Maggi, Lay's, …) the
            # crowdsourced label values on Open Food Facts are more accurate
            # than the model's averaged guess. Override on a hit.
            if looks_branded(name):
                off = await lookup_branded(name, weight_g)
                if off is not None and off.get("calories", 0.0) > 0:
                    macros = off

            display_name = name if any(c.isupper() for c in name) else name.title()
            return NutritionEnrichedIngredient(
                name=display_name,
                weight_g=round(weight_g, 1),
                unit=unit,
                confidence=max(0.0, min(1.0, confidence)),
                calories=macros.get("calories", 0.0),
                protein_g=macros.get("protein_g", 0.0),
                carbs_g=macros.get("carbs_g", 0.0),
                fat_g=macros.get("fat_g", 0.0),
                fiber_g=macros.get("fiber_g", 0.0),
                sugar_g=macros.get("sugar_g", 0.0),
                sodium_mg=macros.get("sodium_mg", 0.0),
            )

        resolved = await asyncio.gather(*(resolve(r) for r in raw_ingredients if isinstance(r, dict)))
        ingredients = [r for r in resolved if r is not None]

        if not ingredients:
            ingredients = [
                NutritionEnrichedIngredient(
                    name=meal_name,
                    weight_g=200.0,
                    unit="g",
                    confidence=overall_conf,
                    calories=0.0, protein_g=0.0, carbs_g=0.0, fat_g=0.0,
                    fiber_g=0.0, sugar_g=0.0, sodium_mg=0.0,
                )
            ]

        return MealAnalysis(
            meal_name=meal_name,
            meal_type=meal_type,
            confidence=max(0.0, min(1.0, overall_conf)),
            ingredients=ingredients,
        )
