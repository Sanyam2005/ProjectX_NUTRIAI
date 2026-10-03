"""Retry the 4 images that 429'd, with a sleep between each, and merge into eval_results.json."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import httpx

API = "http://localhost:8000"
HERE = Path(__file__).resolve().parent.parent
IMAGES = HERE / "test_images"
JSON_OUT = IMAGES / "eval_results.json"

RETRY_FILES = ["sushi.jpg", "stir_fried_eggplant.jpg", "banana.jpg"]  # avocado_toast already merged
SLEEP_S = 30

# Same expectations as eval_accuracy.py
CASES = {
    "sushi.jpg":              {"name_keywords": ["sushi", "nigiri", "maki"],
                               "any_ingredient": ["rice", "salmon", "tuna", "nori", "fish", "sushi"],
                               "kcal_range": (200, 800),
                               "label": "Sushi platter (nigiri + maki + tea)"},
    "stir_fried_eggplant.jpg":{"name_keywords": ["eggplant", "stir-fried", "stir fried", "aubergine"],
                               "any_ingredient": ["eggplant", "aubergine"],
                               "kcal_range": (100, 500),
                               "label": "Stir-fried eggplant"},
    "banana.jpg":             {"name_keywords": ["banana"],
                               "any_ingredient": ["banana"],
                               "kcal_range": (60, 1500),
                               "label": "Banana bunch (market)"},
    "avocado_toast.jpg":      {"name_keywords": ["avocado", "toast", "bread"],
                               "any_ingredient": ["avocado", "bread", "toast", "spinach"],
                               "kcal_range": (200, 700),
                               "label": "Avocado toast with spinach"},
}


def guest_login() -> str:
    r = httpx.post(f"{API}/api/auth/login", json={"mode": "guest"}, timeout=10)
    r.raise_for_status()
    return r.json()["access_token"]


def macro_err(totals: dict) -> float:
    kcal = float(totals.get("calories") or 0)
    if kcal <= 0: return 0.0
    derived = 4 * float(totals.get("protein_g") or 0) + 4 * float(totals.get("carbs_g") or 0) + 9 * float(totals.get("fat_g") or 0)
    return abs(derived - kcal) / kcal


def main() -> int:
    token = guest_login()
    existing = json.loads(JSON_OUT.read_text())
    by_file = {r["file"]: r for r in existing}

    for fname in RETRY_FILES:
        case = CASES[fname]
        path = IMAGES / fname
        # Sleep BEFORE each attempt so we always stay under the per-minute quota,
        # even when previous attempts errored without sleeping.
        print(f"  sleeping {SLEEP_S}s before next call to clear rate-limit window...")
        time.sleep(SLEEP_S)
        print(f"=== {fname} ===")
        try:
            t0 = time.perf_counter()
            with path.open("rb") as f:
                r = httpx.post(
                    f"{API}/api/analyze-meal",
                    headers={"Authorization": f"Bearer {token}"},
                    files={"image": (fname, f, "image/jpeg")},
                    data={"save_image": "false"},
                    timeout=90,
                )
            r.raise_for_status()
            result = r.json()
            elapsed = time.perf_counter() - t0
        except Exception as e:
            print(f"  STILL FAILING: {e}")
            continue

        meal_name = result.get("meal_name", "")
        ingredients = result.get("ingredients") or []
        totals = result.get("totals") or {}
        confidence = float(result.get("confidence") or 0)

        low_name = meal_name.lower()
        ok_name = any(kw.lower() in low_name for kw in case["name_keywords"])
        ing_hits = [t for t in case["any_ingredient"]
                    if any(t.lower() in str(i.get("name", "")).lower() for i in ingredients)]
        ok_ing = bool(ing_hits)
        kcal = round(float(totals.get("calories") or 0))
        lo, hi = case["kcal_range"]
        ok_kcal = lo <= kcal <= hi
        err = macro_err(totals)
        ok_macros = err <= 0.35 and kcal > 0

        print(f"  detected: {meal_name!r} (conf {confidence:.2f})")
        print(f"  totals:   {kcal} kcal | P{totals.get('protein_g')} C{totals.get('carbs_g')} F{totals.get('fat_g')}  ({elapsed:.1f}s)")
        print(f"  CHECK name={'OK' if ok_name else 'MISS'}  ing={'OK' if ok_ing else 'MISS'}  kcal={'OK' if ok_kcal else 'OUT'}  macros={'OK' if ok_macros else 'OFF'}")

        by_file[fname] = {
            "file": fname,
            "label": case["label"],
            "meal_name": meal_name,
            "confidence": confidence,
            "n_ingredients": len(ingredients),
            "kcal": kcal,
            "protein_g": round(float(totals.get("protein_g") or 0), 1),
            "carbs_g":   round(float(totals.get("carbs_g") or 0), 1),
            "fat_g":     round(float(totals.get("fat_g") or 0), 1),
            "elapsed_s": round(elapsed, 2),
            "ok_name": ok_name, "ok_ingredient": ok_ing, "ok_kcal": ok_kcal, "ok_macros": ok_macros,
            "macro_err_pct": round(err * 100, 1),
            "ingredient_matches": ing_hits,
            "ingredient_names": [i.get("name") for i in ingredients],
            "ingredient_weights": [(i.get("name"), i.get("weight_g"), i.get("unit")) for i in ingredients],
        }

    # Write merged back in the same order as the original eval order
    merged = [by_file[r["file"]] for r in existing]
    JSON_OUT.write_text(json.dumps(merged, indent=2))
    print(f"\nMerged eval JSON written to {JSON_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
