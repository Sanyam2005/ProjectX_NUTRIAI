"""Accuracy eval for the NutriAI analyze pipeline.

Walks every JPEG in ``test_images/``, POSTs it to ``/api/analyze-meal`` with a
guest token, and scores the response against expected keywords / ingredients /
calorie ranges. Prints both a per-image breakdown and a summary table.

Run with:
    .\\backend\\.venv\\Scripts\\python.exe scripts\\eval_accuracy.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import httpx

API = "http://localhost:8000"
HERE = Path(__file__).resolve().parent.parent
IMAGES = HERE / "test_images"

# Each case is judged on four checks: meal-name match, ingredient match,
# kcal in plausible range, and macro consistency (4P + 4C + 9F ≈ kcal).
# Ground-truth labels come from actually viewing each downloaded image —
# Pexels-by-keyword search served several mis-tagged photos, so the expected
# values below describe what's ACTUALLY in the photo, not what we asked for.
TEST_CASES: dict[str, dict[str, Any]] = {
    "sneakers_not_food.jpg": {
        "label": "Nike sneakers on tile (not food)",
        "name_keywords": ["meal", "shoe", "sneaker", "no food", "not food"],
        "any_ingredient": [],  # there is no food
        "kcal_range": (0, 50),
    },
    "aloo_paratha.jpg": {
        "label": "Aloo paratha with chutney and onion",
        "name_keywords": ["paratha", "aloo", "flatbread", "bread"],
        "any_ingredient": ["paratha", "flatbread", "potato", "chutney"],
        "kcal_range": (200, 700),
    },
    "paneer_butter_masala.jpg": {
        "label": "Paneer butter masala curry",
        "name_keywords": ["paneer", "butter masala", "curry", "tikka", "makhani"],
        "any_ingredient": ["paneer", "tomato", "gravy", "curry"],
        "kcal_range": (200, 800),
    },
    "pizza.jpg": {
        "label": "Seafood pizza with shrimp, olives, capers, arugula",
        "name_keywords": ["pizza"],
        "any_ingredient": ["pizza", "cheese", "dough", "shrimp", "prawn", "crust"],
        "kcal_range": (200, 2500),  # whole pizza visible — could be very high
    },
    "cheeseburger.jpg": {
        "label": "Cheeseburger with bacon, lettuce, tomato",
        "name_keywords": ["burger", "cheeseburger"],
        "any_ingredient": ["beef", "patty", "bun", "cheese"],
        "kcal_range": (350, 900),
    },
    "mediterranean_salad.jpg": {
        "label": "Mediterranean / Greek salad",
        "name_keywords": ["salad", "mediterranean", "greek"],
        "any_ingredient": ["avocado", "feta", "olive", "tomato"],
        "kcal_range": (200, 800),
    },
    "sushi.jpg": {
        "label": "Sushi platter (nigiri + maki + tea)",
        "name_keywords": ["sushi", "nigiri", "maki"],
        "any_ingredient": ["rice", "salmon", "tuna", "nori", "fish", "sushi"],
        "kcal_range": (200, 800),
    },
    "stir_fried_eggplant.jpg": {
        "label": "Stir-fried eggplant",
        "name_keywords": ["eggplant", "stir-fried", "stir fried", "aubergine"],
        "any_ingredient": ["eggplant", "aubergine"],
        "kcal_range": (100, 500),
    },
    "banana.jpg": {
        "label": "Banana bunch (market)",
        "name_keywords": ["banana"],
        "any_ingredient": ["banana"],
        "kcal_range": (60, 1500),  # could be one to many bananas
    },
    "avocado_toast.jpg": {
        "label": "Avocado toast with spinach",
        "name_keywords": ["avocado", "toast", "bread"],
        "any_ingredient": ["avocado", "bread", "toast", "spinach"],
        "kcal_range": (200, 700),
    },
}


def guest_login() -> str:
    r = httpx.post(f"{API}/api/auth/login", json={"mode": "guest"}, timeout=10)
    r.raise_for_status()
    return r.json()["access_token"]


def analyze(token: str, image_path: Path) -> dict[str, Any]:
    with image_path.open("rb") as f:
        r = httpx.post(
            f"{API}/api/analyze-meal",
            headers={"Authorization": f"Bearer {token}"},
            files={"image": (image_path.name, f, "image/jpeg")},
            data={"save_image": "false"},
            timeout=90,
        )
    r.raise_for_status()
    return r.json()


def match_name(meal_name: str, keywords: list[str]) -> tuple[bool, str | None]:
    low = meal_name.lower()
    for kw in keywords:
        if kw.lower() in low:
            return True, kw
    return False, None


def match_any_ingredient(ingredients: list[dict[str, Any]], targets: list[str]) -> list[str]:
    matched: list[str] = []
    for ing in ingredients:
        name = str(ing.get("name", "")).lower()
        for t in targets:
            if t.lower() in name and t not in matched:
                matched.append(t)
    return matched


_NO_FOOD_SENTINELS = ("no food", "meal", "not food", "unknown")


def is_no_food_response(ingredients: list[dict[str, Any]], kcal: float) -> bool:
    """True when the model correctly refused to identify food in the image.
    Used so non-food test cases (expected ingredient list = []) still score."""
    if kcal > 0 or len(ingredients) != 1:
        return False
    name = str(ingredients[0].get("name", "")).strip().lower()
    return any(name == s or name.startswith(s) for s in _NO_FOOD_SENTINELS)


def macro_consistency(totals: dict[str, Any], expected_range: tuple[int, int]) -> tuple[bool, float]:
    kcal = float(totals.get("calories") or 0)
    # For non-food cases where the model correctly returned 0 kcal, the
    # consistency check is vacuously satisfied (nothing to be inconsistent with).
    if kcal == 0 and expected_range[0] == 0:
        return True, 0.0
    derived = 4 * float(totals.get("protein_g") or 0) + 4 * float(totals.get("carbs_g") or 0) + 9 * float(totals.get("fat_g") or 0)
    if kcal <= 0:
        return False, 0.0
    err = abs(derived - kcal) / kcal
    return err <= 0.35, err


def fmt_macros(t: dict[str, Any]) -> str:
    return (
        f"{round(float(t.get('calories') or 0))} kcal | "
        f"P {round(float(t.get('protein_g') or 0), 1)}g | "
        f"C {round(float(t.get('carbs_g') or 0), 1)}g | "
        f"F {round(float(t.get('fat_g') or 0), 1)}g"
    )


def main() -> int:
    if not IMAGES.is_dir():
        print(f"ERROR: {IMAGES} does not exist")
        return 1

    print("Logging in as guest...")
    token = guest_login()
    print(f"  token len={len(token)}\n")

    rows = []
    for filename, case in TEST_CASES.items():
        path = IMAGES / filename
        if not path.exists():
            print(f"[SKIP] {filename} not in test_images/")
            continue
        print(f"=== {filename} (expected: {case['label']}) ===")
        try:
            t0 = time.perf_counter()
            result = analyze(token, path)
            elapsed = time.perf_counter() - t0
        except httpx.HTTPStatusError as e:
            print(f"  FAILED ({e.response.status_code}): {e.response.text[:200]}")
            rows.append({"file": filename, "error": str(e)})
            continue
        except Exception as e:
            print(f"  EXCEPTION: {e}")
            rows.append({"file": filename, "error": str(e)})
            continue

        meal_name = result.get("meal_name", "")
        ingredients = result.get("ingredients") or []
        totals = result.get("totals") or {}
        confidence = float(result.get("confidence") or 0)

        ok_name, hit_kw = match_name(meal_name, case["name_keywords"])
        ing_hits = match_any_ingredient(ingredients, case["any_ingredient"])
        kcal = round(float(totals.get("calories") or 0))
        lo, hi = case["kcal_range"]
        # Non-food test cases (expected ingredient list = []) pass when the
        # model correctly refuses to identify food.
        no_food_pass = not case["any_ingredient"] and is_no_food_response(ingredients, kcal)
        ok_ing = bool(ing_hits) or no_food_pass
        ok_kcal = lo <= kcal <= hi
        ok_macros, macro_err = macro_consistency(totals, case["kcal_range"])

        print(f"  detected:    {meal_name!r}  (conf {confidence:.2f})")
        print(f"  ingredients: {[i.get('name') for i in ingredients]}")
        print(f"  totals:      {fmt_macros(totals)}")
        print(f"  elapsed:     {elapsed:.2f}s")
        print(
            f"  CHECK name={'OK' if ok_name else 'MISS'}({hit_kw})  "
            f"ing={'OK' if ok_ing else 'MISS'}({ing_hits or '-'})  "
            f"kcal={'OK' if ok_kcal else 'OUT'}({kcal} vs {lo}-{hi})  "
            f"macros={'OK' if ok_macros else 'OFF'}(err {macro_err*100:.1f}%)"
        )
        print()

        rows.append({
            "file": filename,
            "label": case["label"],
            "meal_name": meal_name,
            "confidence": confidence,
            "n_ingredients": len(ingredients),
            "kcal": kcal,
            "protein_g": round(float(totals.get("protein_g") or 0), 1),
            "carbs_g": round(float(totals.get("carbs_g") or 0), 1),
            "fat_g": round(float(totals.get("fat_g") or 0), 1),
            "elapsed_s": round(elapsed, 2),
            "ok_name": ok_name,
            "ok_ingredient": ok_ing,
            "ok_kcal": ok_kcal,
            "ok_macros": ok_macros,
            "macro_err_pct": round(macro_err * 100, 1),
            "ingredient_matches": ing_hits,
            "ingredient_names": [i.get("name") for i in ingredients],
            "ingredient_weights": [(i.get("name"), i.get("weight_g"), i.get("unit")) for i in ingredients],
        })

    # Summary
    if not rows:
        print("No results.")
        return 1

    print("\n=== SUMMARY ===")
    succ = [r for r in rows if "error" not in r]
    name_ok = sum(1 for r in succ if r["ok_name"])
    ing_ok = sum(1 for r in succ if r["ok_ingredient"])
    kcal_ok = sum(1 for r in succ if r["ok_kcal"])
    macros_ok = sum(1 for r in succ if r["ok_macros"])
    n = len(succ)
    times = [r["elapsed_s"] for r in succ]
    avg_t = sum(times) / len(times) if times else 0
    min_t = min(times) if times else 0
    max_t = max(times) if times else 0
    print(f"  Images analyzed     : {n}/{len(rows)}")
    print(f"  Meal-name match     : {name_ok}/{n}")
    print(f"  Ingredient match    : {ing_ok}/{n}")
    print(f"  Calories in range   : {kcal_ok}/{n}")
    print(f"  Macro consistency   : {macros_ok}/{n}")
    print(f"  Latency             : avg {avg_t:.2f}s, min {min_t:.2f}s, max {max_t:.2f}s")

    print("\n=== TABLE ===")
    print(f"{'file':22} {'detected':30} {'kcal':>6} {'P':>5} {'C':>5} {'F':>5} {'N':>3}  checks")
    print("-" * 100)
    for r in rows:
        if "error" in r:
            print(f"{r['file']:22} ERROR: {r['error'][:60]}")
            continue
        checks = (
            ("N" if r["ok_name"] else "n") +
            ("I" if r["ok_ingredient"] else "i") +
            ("K" if r["ok_kcal"] else "k") +
            ("M" if r["ok_macros"] else "m")
        )
        print(
            f"{r['file']:22} {r['meal_name'][:30]:30} "
            f"{r['kcal']:>6} {r['protein_g']:>5} {r['carbs_g']:>5} {r['fat_g']:>5} "
            f"{r['n_ingredients']:>3}  {checks}"
        )

    # Save JSON to disk for inspection
    out = HERE / "test_images" / "eval_results.json"
    out.write_text(json.dumps(rows, indent=2))
    print(f"\nFull JSON written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
