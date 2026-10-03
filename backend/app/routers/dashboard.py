from datetime import date, datetime, time, timedelta
from typing import Any

from fastapi import APIRouter
from sqlalchemy import desc, func, select
from sqlalchemy.orm import selectinload

from app.deps import DB, CurrentUser
from app.models import Goal, Meal, WaterLog
from app.utils import today_ist

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _day_bounds(d: date) -> tuple[datetime, datetime]:
    start = datetime.combine(d, time.min)
    end = datetime.combine(d, time.max)
    return start, end


@router.get("")
async def dashboard(user: CurrentUser, db: DB) -> dict[str, Any]:
    today = today_ist()
    start, end = _day_bounds(today)

    # Today's totals
    todays_meals = (
        await db.execute(
            select(Meal)
            .where(Meal.user_id == user.id, Meal.consumed_at >= start, Meal.consumed_at <= end)
            .order_by(desc(Meal.consumed_at))
        )
    ).scalars().all()

    totals = {
        "calories": round(sum(m.calories for m in todays_meals), 1),
        "protein_g": round(sum(m.protein_g for m in todays_meals), 1),
        "carbs_g": round(sum(m.carbs_g for m in todays_meals), 1),
        "fat_g": round(sum(m.fat_g for m in todays_meals), 1),
        "fiber_g": round(sum(m.fiber_g for m in todays_meals), 1),
    }

    water_today = (
        await db.execute(
            select(func.coalesce(func.sum(WaterLog.amount_ml), 0)).where(
                WaterLog.user_id == user.id,
                WaterLog.recorded_at >= start,
                WaterLog.recorded_at <= end,
            )
        )
    ).scalar_one()

    goal_row = (await db.execute(select(Goal).where(Goal.user_id == user.id))).scalar_one_or_none()
    goal = {
        "target_calories": goal_row.target_calories if goal_row else 2000,
        "target_protein_g": goal_row.target_protein_g if goal_row else 80,
        "target_carbs_g": goal_row.target_carbs_g if goal_row else 250,
        "target_fat_g": goal_row.target_fat_g if goal_row else 65,
        "target_fiber_g": goal_row.target_fiber_g if goal_row else 30,
        "target_water_ml": goal_row.target_water_ml if goal_row else 2500,
        "weight_kg": goal_row.weight_kg if goal_row else None,
        "target_weight_kg": goal_row.target_weight_kg if goal_row else None,
    }

    # Recent meals (any day)
    recent = (
        await db.execute(
            select(Meal).options(selectinload(Meal.ingredients))
            .where(Meal.user_id == user.id)
            .order_by(desc(Meal.consumed_at))
            .limit(5)
        )
    ).scalars().all()

    # Streak: consecutive past days (incl. today) with at least one meal logged.
    distinct_days = (
        await db.execute(
            select(func.date(Meal.consumed_at).label("d"))
            .where(Meal.user_id == user.id)
            .group_by("d")
            .order_by(desc("d"))
            .limit(60)
        )
    ).all()
    logged = {(row[0] if isinstance(row[0], date) else date.fromisoformat(str(row[0]))) for row in distinct_days}
    streak = 0
    cursor = today
    while cursor in logged:
        streak += 1
        cursor -= timedelta(days=1)

    return {
        "date": today.isoformat(),
        "totals": totals,
        "water_ml": float(water_today),
        "goal": goal,
        "calories_remaining": max(goal["target_calories"] - totals["calories"], 0),
        "streak": streak,
        "recent_meals": [
            {
                "id": m.id,
                "name": m.name,
                "meal_type": m.meal_type,
                "image_url": m.image_url,
                "calories": m.calories,
                "consumed_at": m.consumed_at.isoformat(),
            }
            for m in recent
        ],
    }
