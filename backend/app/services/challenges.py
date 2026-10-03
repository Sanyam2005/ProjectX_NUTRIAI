"""Wellness challenge catalog + progress / leaderboard computation.

Challenges are defined declaratively here so the catalog can evolve without
DB migrations. The only persisted state is opt-in (``ChallengeParticipant``).

Progress is computed on the fly from the user's meals + water logs for the
current ISO week (Mon–Sun). Leaderboards rank participants by their progress
percentage within the active week.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Literal

from app.utils import today_ist

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChallengeParticipant, Goal, Meal, MealIngredient, User, WaterLog


Metric = Literal["protein_days", "water_days", "veggie_meals", "log_days", "balanced_days"]


@dataclass(slots=True, frozen=True)
class ChallengeDef:
    code: str
    title: str
    description: str
    icon: str
    metric: Metric
    target: int           # e.g. "5 days", "10 meals"
    unit: str             # short label for UI ("days", "meals")


CATALOG: list[ChallengeDef] = [
    ChallengeDef(
        "protein_power_week", "Protein Power Week",
        "Hit your protein target on 5 of 7 days this week.",
        "💪", "protein_days", 5, "days",
    ),
    ChallengeDef(
        "hydration_hero", "Hydration Hero",
        "Hit your water goal on 5 of 7 days this week.",
        "💧", "water_days", 5, "days",
    ),
    ChallengeDef(
        "veggie_week", "Veggie Week",
        "Include a vegetable in 10 meals this week.",
        "🥗", "veggie_meals", 10, "meals",
    ),
    ChallengeDef(
        "daily_logger", "Daily Logger",
        "Log at least one meal every day this week.",
        "📒", "log_days", 7, "days",
    ),
    ChallengeDef(
        "balanced_week", "Balanced Week",
        "Land within ±10% of your calorie target on 4 days.",
        "⚖️", "balanced_days", 4, "days",
    ),
]

_BY_CODE = {c.code: c for c in CATALOG}

_VEG_KEYWORDS = {
    "salad", "veg", "vegetable", "spinach", "palak", "broccoli", "cauliflower", "gobi",
    "carrot", "tomato", "cucumber", "lettuce", "kale", "cabbage", "peas", "matar",
    "beans", "bhindi", "okra", "lauki", "karela", "tinda", "baingan", "brinjal",
    "methi", "fenugreek", "onion", "capsicum", "mushroom", "kachumber", "raita",
}


def current_week_bounds(today: date | None = None) -> tuple[date, date]:
    today = today or today_ist()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def _is_veg(name: str) -> bool:
    low = name.lower()
    return any(k in low for k in _VEG_KEYWORDS)


async def _goal_for(db: AsyncSession, user_id: str) -> Goal | None:
    return (await db.execute(select(Goal).where(Goal.user_id == user_id))).scalar_one_or_none()


async def _progress(db: AsyncSession, user_id: str, defn: ChallengeDef) -> int:
    monday, sunday = current_week_bounds()
    start = datetime.combine(monday, time.min)
    end = datetime.combine(sunday, time.max)

    if defn.metric == "log_days":
        rows = (await db.execute(
            select(func.distinct(func.date(Meal.consumed_at)))
            .where(Meal.user_id == user_id, Meal.consumed_at >= start, Meal.consumed_at <= end)
        )).scalars().all()
        return len(rows)

    if defn.metric == "veggie_meals":
        # Count distinct meals that contain at least one veggie ingredient.
        names = (await db.execute(
            select(Meal.id, MealIngredient.name)
            .join(MealIngredient, MealIngredient.meal_id == Meal.id)
            .where(Meal.user_id == user_id, Meal.consumed_at >= start, Meal.consumed_at <= end)
        )).all()
        veg_meals: set[str] = set()
        for mid, name in names:
            if _is_veg(name):
                veg_meals.add(mid)
        return len(veg_meals)

    if defn.metric in ("protein_days", "balanced_days"):
        goal = await _goal_for(db, user_id)
        target_protein = goal.target_protein_g if goal else 80
        target_cal = goal.target_calories if goal else 2000
        count = 0
        for i in range(7):
            d = monday + timedelta(days=i)
            d_start = datetime.combine(d, time.min)
            d_end = datetime.combine(d, time.max)
            if defn.metric == "protein_days":
                tot = (await db.execute(
                    select(func.coalesce(func.sum(Meal.protein_g), 0))
                    .where(Meal.user_id == user_id, Meal.consumed_at >= d_start, Meal.consumed_at <= d_end)
                )).scalar_one()
                if float(tot or 0) >= target_protein:
                    count += 1
            else:
                tot = (await db.execute(
                    select(func.coalesce(func.sum(Meal.calories), 0))
                    .where(Meal.user_id == user_id, Meal.consumed_at >= d_start, Meal.consumed_at <= d_end)
                )).scalar_one()
                cal = float(tot or 0)
                if cal > 0 and target_cal * 0.9 <= cal <= target_cal * 1.1:
                    count += 1
        return count

    if defn.metric == "water_days":
        goal = await _goal_for(db, user_id)
        target_water = goal.target_water_ml if goal else 2500
        count = 0
        for i in range(7):
            d = monday + timedelta(days=i)
            d_start = datetime.combine(d, time.min)
            d_end = datetime.combine(d, time.max)
            tot = (await db.execute(
                select(func.coalesce(func.sum(WaterLog.amount_ml), 0))
                .where(WaterLog.user_id == user_id, WaterLog.recorded_at >= d_start, WaterLog.recorded_at <= d_end)
            )).scalar_one()
            if float(tot or 0) >= target_water:
                count += 1
        return count

    return 0


async def list_for_user(db: AsyncSession, user_id: str) -> list[dict]:
    monday, sunday = current_week_bounds()
    joined_codes = set((await db.execute(
        select(ChallengeParticipant.challenge_code).where(ChallengeParticipant.user_id == user_id)
    )).scalars().all())

    out: list[dict] = []
    for defn in CATALOG:
        progress = await _progress(db, user_id, defn) if defn.code in joined_codes else 0
        out.append({
            "code": defn.code,
            "title": defn.title,
            "description": defn.description,
            "icon": defn.icon,
            "metric": defn.metric,
            "target": defn.target,
            "unit": defn.unit,
            "joined": defn.code in joined_codes,
            "progress": progress,
            "completed": progress >= defn.target,
            "starts_on": monday.isoformat(),
            "ends_on":   sunday.isoformat(),
        })
    return out


async def join(db: AsyncSession, user_id: str, code: str) -> bool:
    if code not in _BY_CODE:
        return False
    exists = (await db.execute(
        select(ChallengeParticipant.id).where(
            ChallengeParticipant.user_id == user_id,
            ChallengeParticipant.challenge_code == code,
        )
    )).scalar_one_or_none()
    if exists:
        return True
    db.add(ChallengeParticipant(user_id=user_id, challenge_code=code))
    await db.flush()
    return True


async def leave(db: AsyncSession, user_id: str, code: str) -> bool:
    res = await db.execute(
        select(ChallengeParticipant).where(
            ChallengeParticipant.user_id == user_id,
            ChallengeParticipant.challenge_code == code,
        )
    )
    p = res.scalar_one_or_none()
    if p is None:
        return False
    await db.delete(p)
    await db.flush()
    return True


async def leaderboard(db: AsyncSession, code: str, *, current_user_id: str, limit: int = 25) -> dict:
    defn = _BY_CODE.get(code)
    if defn is None:
        return {"code": code, "entries": [], "current_user_rank": None}

    rows = (await db.execute(
        select(ChallengeParticipant.user_id, User.name, User.is_guest)
        .join(User, User.id == ChallengeParticipant.user_id)
        .where(ChallengeParticipant.challenge_code == code)
    )).all()

    entries = []
    for uid, name, is_guest in rows:
        progress = await _progress(db, uid, defn)
        entries.append({
            "user_id": uid,
            "name": ("Guest" if is_guest else (name or "User")),
            "progress": progress,
            "target": defn.target,
            "completed": progress >= defn.target,
            "is_self": uid == current_user_id,
        })
    entries.sort(key=lambda e: (-e["progress"], e["name"].lower()))
    for idx, e in enumerate(entries, start=1):
        e["rank"] = idx

    self_rank = next((e["rank"] for e in entries if e["is_self"]), None)
    return {
        "code": code,
        "title": defn.title,
        "icon": defn.icon,
        "unit": defn.unit,
        "target": defn.target,
        "entries": entries[:limit],
        "current_user_rank": self_rank,
    }
