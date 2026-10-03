from datetime import date, datetime, timedelta
from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import asc, select

from app.deps import DB, CurrentUser
from app.models import Goal, WaterLog, WeightHistory
from app.utils import now_ist

router = APIRouter(prefix="/api", tags=["tracking"])

BmiCategory = Literal["underweight", "normal", "overweight", "obese"]


class WaterIn(BaseModel):
    amount_ml: float = Field(gt=0, le=5000)
    recorded_at: datetime | None = None


class WeightIn(BaseModel):
    weight_kg: float = Field(gt=0, le=500)
    recorded_at: datetime | None = None


def _bmi(weight_kg: float, height_cm: float) -> float:
    h_m = height_cm / 100.0
    if h_m <= 0:
        return 0.0
    return weight_kg / (h_m * h_m)


def _bmi_category(bmi: float) -> BmiCategory:
    if bmi < 18.5:
        return "underweight"
    if bmi < 25.0:
        return "normal"
    if bmi < 30.0:
        return "overweight"
    return "obese"


@router.post("/water", status_code=201)
async def log_water(payload: WaterIn, user: CurrentUser, db: DB) -> dict:
    entry = WaterLog(
        user_id=user.id,
        amount_ml=payload.amount_ml,
        recorded_at=payload.recorded_at or now_ist(),
    )
    db.add(entry)
    await db.commit()
    return {"id": entry.id, "amount_ml": entry.amount_ml, "recorded_at": entry.recorded_at.isoformat()}


@router.post("/weight", status_code=201)
async def log_weight(payload: WeightIn, user: CurrentUser, db: DB) -> dict:
    entry = WeightHistory(
        user_id=user.id,
        weight_kg=payload.weight_kg,
        recorded_at=payload.recorded_at or now_ist(),
    )
    db.add(entry)
    await db.commit()
    return {"id": entry.id, "weight_kg": entry.weight_kg, "recorded_at": entry.recorded_at.isoformat()}


@router.get("/weight/report")
async def weight_report(user: CurrentUser, db: DB) -> dict[str, Any]:
    """Full weight + BMI report for the signed-in user.

    BMI requires height (stored on the user's Goal). If height is missing the
    BMI fields come back as null and the frontend prompts the user to set it.
    """
    goal = (await db.execute(select(Goal).where(Goal.user_id == user.id))).scalar_one_or_none()
    height_cm = goal.height_cm if goal else None
    target_weight_kg = goal.target_weight_kg if goal else None

    rows = (await db.execute(
        select(WeightHistory)
        .where(WeightHistory.user_id == user.id)
        .order_by(asc(WeightHistory.recorded_at))
    )).scalars().all()

    series: list[dict[str, Any]] = []
    for r in rows:
        bmi_val = round(_bmi(r.weight_kg, height_cm), 1) if height_cm else None
        series.append({
            "date": r.recorded_at.date().isoformat(),
            "weight_kg": round(r.weight_kg, 1),
            "bmi": bmi_val,
        })

    current = series[-1] if series else None
    first = series[0] if series else None

    change_total = None
    change_pct = None
    if current and first and current["date"] != first["date"]:
        change_total = round(current["weight_kg"] - first["weight_kg"], 1)
        if first["weight_kg"]:
            change_pct = round((change_total / first["weight_kg"]) * 100.0, 1)

    def _change_vs(days: int) -> float | None:
        if not current:
            return None
        cutoff = date.today() - timedelta(days=days)
        # Latest entry on or before cutoff.
        for r in reversed(rows):
            if r.recorded_at.date() <= cutoff:
                return round(current["weight_kg"] - r.weight_kg, 1)
        return None

    current_bmi = current["bmi"] if current else None
    target_bmi = (
        round(_bmi(target_weight_kg, height_cm), 1)
        if target_weight_kg and height_cm
        else None
    )

    return {
        "height_cm": height_cm,
        "current_weight_kg": current["weight_kg"] if current else None,
        "current_bmi": current_bmi,
        "bmi_category": _bmi_category(current_bmi) if current_bmi else None,
        "target_weight_kg": target_weight_kg,
        "target_bmi": target_bmi,
        "change_kg_total": change_total,
        "change_pct_total": change_pct,
        "change_kg_7d": _change_vs(7),
        "change_kg_30d": _change_vs(30),
        "series": series,
    }
