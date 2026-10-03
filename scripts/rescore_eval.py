"""Recompute the pass/fail flags in eval_results.json against the current
TEST_CASES dict in eval_accuracy.py, without re-calling the model.

Used after editing keywords / kcal ranges so the JSON + chart match the
ground truth without burning API calls.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "scripts"))
from eval_accuracy import TEST_CASES, is_no_food_response, macro_consistency  # noqa: E402

JSON = HERE / "test_images" / "eval_results.json"


def match_name(meal_name: str, keywords: list[str]) -> bool:
    low = meal_name.lower()
    return any(kw.lower() in low for kw in keywords)


def match_any_ingredient(ingredient_names: list[str], targets: list[str]) -> list[str]:
    hits: list[str] = []
    for name in ingredient_names:
        low = str(name).lower()
        for t in targets:
            if t.lower() in low and t not in hits:
                hits.append(t)
    return hits


def main() -> int:
    data = json.loads(JSON.read_text())
    changed = 0
    for row in data:
        case = TEST_CASES.get(row["file"])
        if case is None:
            print(f"  SKIP (no case): {row['file']}")
            continue
        before = (row["ok_name"], row["ok_ingredient"], row["ok_kcal"], row["ok_macros"])

        row["ok_name"] = match_name(row["meal_name"], case["name_keywords"])
        hits = match_any_ingredient(row["ingredient_names"], case["any_ingredient"])
        # Non-food test cases pass when the model correctly refused to identify food.
        sentinel_ingredients = [{"name": n} for n in row["ingredient_names"]]
        no_food_pass = not case["any_ingredient"] and is_no_food_response(sentinel_ingredients, row["kcal"])
        row["ok_ingredient"] = bool(hits) or no_food_pass
        row["ingredient_matches"] = hits
        lo, hi = case["kcal_range"]
        row["ok_kcal"] = lo <= row["kcal"] <= hi
        ok_m, _ = macro_consistency(
            {"calories": row["kcal"], "protein_g": row["protein_g"],
             "carbs_g": row["carbs_g"], "fat_g": row["fat_g"]},
            case["kcal_range"],
        )
        row["ok_macros"] = ok_m

        after = (row["ok_name"], row["ok_ingredient"], row["ok_kcal"], row["ok_macros"])
        if before != after:
            changed += 1
            print(f"  CHANGED {row['file']:30s} {before} -> {after}")
        else:
            print(f"  unchanged {row['file']}")

    JSON.write_text(json.dumps(data, indent=2))
    print(f"\nRewrote {JSON} ({changed} rows changed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
