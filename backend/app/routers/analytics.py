from collections import defaultdict
from datetime import date, datetime, time, timedelta
from typing import Any, Literal

from fastapi import APIRouter, Query
from sqlalchemy import desc, func, select

from app.deps import DB, CurrentUser
from app.models import Goal, Meal, MealIngredient, WeightHistory
from app.utils import today_ist

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

Range = Literal["7d", "30d", "90d"]


def _start_for(range_: Range) -> datetime:
    days = {"7d": 7, "30d": 30, "90d": 90}[range_]
    return datetime.combine(today_ist() - timedelta(days=days - 1), time.min)


@router.get("")
async def analytics(
    user: CurrentUser,
    db: DB,
    range_: Range = Query(default="7d", alias="range"),
) -> dict[str, Any]:
    start = _start_for(range_)
    today = today_ist()

    rows = (
        await db.execute(
            select(Meal).where(Meal.user_id == user.id, Meal.consumed_at >= start)
        )
    ).scalars().all()

    # Daily series, including zero-fill days.
    by_day: dict[date, dict[str, float]] = defaultdict(
        lambda: {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0, "fiber_g": 0.0}
    )
    days_count = (today - start.date()).days + 1
    for i in range(days_count):
        by_day[start.date() + timedelta(days=i)] = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0, "fiber_g": 0.0}

    for m in rows:
        d = m.consumed_at.date()
        bucket = by_day[d]
        bucket["calories"] += m.calories
        bucket["protein_g"] += m.protein_g
        bucket["carbs_g"] += m.carbs_g
        bucket["fat_g"] += m.fat_g
        bucket["fiber_g"] += m.fiber_g

    series = [
        {"date": d.isoformat(), **{k: round(v, 1) for k, v in totals.items()}}
        for d, totals in sorted(by_day.items())
    ]

    # Most consumed foods
    ing_rows = (
        await db.execute(
            select(MealIngredient.name, func.count().label("c"), func.sum(MealIngredient.calories).label("kcal"))
            .join(Meal, Meal.id == MealIngredient.meal_id)
            .where(Meal.user_id == user.id, Meal.consumed_at >= start)
            .group_by(MealIngredient.name)
            .order_by(desc("c"))
            .limit(10)
        )
    ).all()
    top_foods = [{"name": r[0], "count": int(r[1]), "calories": round(float(r[2] or 0), 1)} for r in ing_rows]

    avg_calories = round(sum(d["calories"] for d in series) / max(len(series), 1), 1)

    # Weight series
    weight_rows = (
        await db.execute(
            select(WeightHistory.recorded_at, WeightHistory.weight_kg)
            .where(WeightHistory.user_id == user.id, WeightHistory.recorded_at >= start)
            .order_by(WeightHistory.recorded_at)
        )
    ).all()
    weight_series = [{"date": r[0].date().isoformat(), "weight_kg": r[1]} for r in weight_rows]

    # Healthy score: 0–100 blend of fiber%, protein%, and "within goal" days.
    goal_row = (await db.execute(select(Goal).where(Goal.user_id == user.id))).scalar_one_or_none()
    target_cal = goal_row.target_calories if goal_row else 2000
    target_protein = goal_row.target_protein_g if goal_row else 80
    target_fiber = goal_row.target_fiber_g if goal_row else 30

    within_goal_days = sum(1 for d in series if 0 < d["calories"] <= target_cal * 1.1)
    avg_protein = sum(d["protein_g"] for d in series) / max(len(series), 1)
    avg_fiber = sum(d["fiber_g"] for d in series) / max(len(series), 1)
    score = (
        min(within_goal_days / max(len(series), 1), 1.0) * 40
        + min(avg_protein / max(target_protein, 1), 1.0) * 30
        + min(avg_fiber / max(target_fiber, 1), 1.0) * 30
    )

    return {
        "range": range_,
        "series": series,
        "avg_calories": avg_calories,
        "top_foods": top_foods,
        "weight_series": weight_series,
        "healthy_score": round(score, 1),
    }
