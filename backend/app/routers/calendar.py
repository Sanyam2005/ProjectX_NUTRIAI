from calendar import monthrange
from datetime import date, datetime, time, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.deps import DB, CurrentUser
from app.models import Goal, Meal, WaterLog
from app.utils import today_ist

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


@router.get("")
async def month(
    user: CurrentUser,
    db: DB,
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
) -> dict[str, Any]:
    try:
        first = date(year, month, 1)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid year/month") from exc

    days_in_month = monthrange(year, month)[1]
    last = date(year, month, days_in_month)

    start = datetime.combine(first, time.min)
    end = datetime.combine(last, time.max)

    rows = (await db.execute(
        select(
            func.date(Meal.consumed_at).label("d"),
            func.coalesce(func.sum(Meal.calories), 0),
            func.coalesce(func.sum(Meal.protein_g), 0),
            func.coalesce(func.sum(Meal.carbs_g), 0),
            func.coalesce(func.sum(Meal.fat_g), 0),
            func.coalesce(func.sum(Meal.fiber_g), 0),
            func.count(Meal.id),
        )
        .where(Meal.user_id == user.id, Meal.consumed_at >= start, Meal.consumed_at <= end)
        .group_by("d")
    )).all()

    water_rows = (await db.execute(
        select(
            func.date(WaterLog.recorded_at).label("d"),
            func.coalesce(func.sum(WaterLog.amount_ml), 0),
        )
        .where(WaterLog.user_id == user.id, WaterLog.recorded_at >= start, WaterLog.recorded_at <= end)
        .group_by("d")
    )).all()

    def to_date(v: Any) -> date:
        return v if isinstance(v, date) else date.fromisoformat(str(v))

    by_day: dict[date, dict[str, float]] = {}
    for d, cal, prot, carbs, fat, fiber, count in rows:
        by_day[to_date(d)] = {
            "calories": float(cal), "protein_g": float(prot),
            "carbs_g": float(carbs), "fat_g": float(fat), "fiber_g": float(fiber),
            "meal_count": int(count),
        }
    water_by_day = {to_date(d): float(ml) for d, ml in water_rows}

    goal = (await db.execute(select(Goal).where(Goal.user_id == user.id))).scalar_one_or_none()
    target_cal = goal.target_calories if goal else 2000
    target_water = goal.target_water_ml if goal else 2500

    today = today_ist()
    days_out: list[dict[str, Any]] = []
    for i in range(days_in_month):
        d = first + timedelta(days=i)
        bucket = by_day.get(d, {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0, "fiber_g": 0.0, "meal_count": 0})
        cal = bucket["calories"]
        water = water_by_day.get(d, 0.0)

        if d > today:
            status = "future"
        elif bucket["meal_count"] == 0:
            status = "empty"
        elif cal > target_cal * 1.1:
            status = "over"
        elif cal < target_cal * 0.6:
            status = "under"
        else:
            status = "ok"

        days_out.append({
            "date": d.isoformat(),
            "status": status,
            "calories": round(cal, 1),
            "protein_g": round(bucket["protein_g"], 1),
            "carbs_g": round(bucket["carbs_g"], 1),
            "fat_g": round(bucket["fat_g"], 1),
            "fiber_g": round(bucket["fiber_g"], 1),
            "meal_count": bucket["meal_count"],
            "water_ml": round(water, 0),
            "target_calories": target_cal,
            "target_water_ml": target_water,
        })

    healthy_days = sum(1 for d in days_out if d["status"] == "ok")
    over_days    = sum(1 for d in days_out if d["status"] == "over")
    skipped_days = sum(1 for d in days_out if d["status"] in ("under", "empty") and d["date"] <= today.isoformat())

    return {
        "year": year,
        "month": month,
        "first_weekday": first.weekday(),
        "days": days_out,
        "summary": {
            "healthy_days": healthy_days,
            "over_days": over_days,
            "skipped_days": skipped_days,
            "logged_days": sum(1 for d in days_out if d["meal_count"] > 0),
        },
    }
