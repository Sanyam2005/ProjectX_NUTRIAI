"""Achievement catalog + awarder.

Achievements are defined declaratively here so the catalog can evolve without
DB migrations. Each entry has an idempotent `code` — once a row exists in the
``achievements`` table for ``(user_id, code)``, we never insert again.

``check_and_award`` is called from the meal-save path. It is intentionally
forgiving and best-effort: failures don't break the user's save flow.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from app.utils import today_ist

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Achievement, Meal, MealIngredient, WaterLog

log = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class AchievementDef:
    code: str
    title: str
    description: str
    icon: str


CATALOG: list[AchievementDef] = [
    AchievementDef("first_meal",      "First Bite",       "Logged your very first meal.",                   "🍽️"),
    AchievementDef("streak_3",        "On a Roll",        "Logged meals on 3 days in a row.",               "🔥"),
    AchievementDef("streak_7",        "Streak Star",      "A full week of consistent logging.",             "⭐"),
    AchievementDef("streak_30",       "Habit Built",      "30-day logging streak — this is your routine.", "🏆"),
    AchievementDef("veggie_hero",     "Veggie Hero",      "Added veggies to 10 meals.",                     "🥗"),
    AchievementDef("protein_pro",     "Protein Pro",      "Hit your protein goal 5 days in a row.",        "💪"),
    AchievementDef("hydration_pro",   "Hydration Pro",    "Hit your water goal 3 days in a row.",          "💧"),
    AchievementDef("early_logger",    "Early Logger",     "Logged breakfast before 9 AM.",                  "🌅"),
    AchievementDef("balanced_day",    "Balanced Day",     "Hit calories within 10% of goal on a day.",     "⚖️"),
    AchievementDef("explorer",        "Explorer",         "Logged 15 different foods.",                     "🧭"),
]

_BY_CODE = {a.code: a for a in CATALOG}

_VEG_KEYWORDS = {
    "salad", "veg", "vegetable", "spinach", "palak", "broccoli", "cauliflower", "gobi",
    "carrot", "tomato", "cucumber", "lettuce", "kale", "cabbage", "peas", "matar",
    "beans", "bhindi", "okra", "lauki", "karela", "tinda", "baingan", "brinjal",
    "methi", "fenugreek", "onion", "capsicum", "mushroom", "kachumber", "raita",
}


def _is_veggie(name: str) -> bool:
    low = name.lower()
    return any(k in low for k in _VEG_KEYWORDS)


async def _has(db: AsyncSession, user_id: str, code: str) -> bool:
    res = await db.execute(
        select(Achievement.id).where(Achievement.user_id == user_id, Achievement.code == code).limit(1)
    )
    return res.scalar_one_or_none() is not None


async def _award(db: AsyncSession, user_id: str, code: str) -> None:
    if code not in _BY_CODE:
        return
    if await _has(db, user_id, code):
        return
    defn = _BY_CODE[code]
    db.add(Achievement(
        user_id=user_id, code=code,
        title=defn.title, description=defn.description, icon=defn.icon,
    ))


async def _logging_streak(db: AsyncSession, user_id: str) -> int:
    rows = (await db.execute(
        select(func.date(Meal.consumed_at).label("d"))
        .where(Meal.user_id == user_id)
        .group_by("d")
        .order_by(desc("d"))
        .limit(60)
    )).all()
    days: set[date] = set()
    for row in rows:
        v = row[0]
        if isinstance(v, date):
            days.add(v)
        else:
            try:
                days.add(date.fromisoformat(str(v)))
            except Exception:
                pass
    streak = 0
    cursor = today_ist()
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


async def _veg_count(db: AsyncSession, user_id: str) -> int:
    rows = (await db.execute(
        select(MealIngredient.name)
        .join(Meal, Meal.id == MealIngredient.meal_id)
        .where(Meal.user_id == user_id)
    )).scalars().all()
    return sum(1 for n in rows if _is_veggie(n))


async def _distinct_foods(db: AsyncSession, user_id: str) -> int:
    res = (await db.execute(
        select(func.count(func.distinct(func.lower(MealIngredient.name))))
        .join(Meal, Meal.id == MealIngredient.meal_id)
        .where(Meal.user_id == user_id)
    )).scalar_one()
    return int(res or 0)


async def _balanced_day(db: AsyncSession, user_id: str, target_cal: int) -> bool:
    if target_cal <= 0:
        return False
    today = today_ist()
    start = datetime.combine(today, time.min)
    end = datetime.combine(today, time.max)
    res = (await db.execute(
        select(func.coalesce(func.sum(Meal.calories), 0))
        .where(Meal.user_id == user_id, Meal.consumed_at >= start, Meal.consumed_at <= end)
    )).scalar_one()
    consumed = float(res or 0)
    return 0 < consumed <= target_cal * 1.1 and consumed >= target_cal * 0.9


async def _hydration_streak(db: AsyncSession, user_id: str, target_ml: int) -> int:
    if target_ml <= 0:
        return 0
    today = today_ist()
    streak = 0
    for i in range(0, 14):
        d = today - timedelta(days=i)
        start = datetime.combine(d, time.min)
        end = datetime.combine(d, time.max)
        res = (await db.execute(
            select(func.coalesce(func.sum(WaterLog.amount_ml), 0))
            .where(WaterLog.user_id == user_id, WaterLog.recorded_at >= start, WaterLog.recorded_at <= end)
        )).scalar_one()
        total = float(res or 0)
        if total >= target_ml:
            streak += 1
        else:
            break
    return streak


async def _protein_streak(db: AsyncSession, user_id: str, target_g: int) -> int:
    if target_g <= 0:
        return 0
    today = today_ist()
    streak = 0
    for i in range(0, 14):
        d = today - timedelta(days=i)
        start = datetime.combine(d, time.min)
        end = datetime.combine(d, time.max)
        res = (await db.execute(
            select(func.coalesce(func.sum(Meal.protein_g), 0))
            .where(Meal.user_id == user_id, Meal.consumed_at >= start, Meal.consumed_at <= end)
        )).scalar_one()
        total = float(res or 0)
        if total >= target_g:
            streak += 1
        else:
            break
    return streak


async def check_and_award(
    db: AsyncSession,
    user_id: str,
    *,
    target_calories: int,
    target_protein_g: int,
    target_water_ml: int,
    last_meal: Meal | None = None,
) -> list[str]:
    """Re-evaluate all achievements for the user; award any newly earned.

    Returns the list of newly awarded codes (may be empty). Idempotent and
    safe to call after every meal save.
    """
    newly: list[str] = []

    try:
        # first_meal: any meal exists
        meal_count = (await db.execute(
            select(func.count(Meal.id)).where(Meal.user_id == user_id)
        )).scalar_one()
        if int(meal_count or 0) >= 1 and not await _has(db, user_id, "first_meal"):
            await _award(db, user_id, "first_meal")
            newly.append("first_meal")

        # streaks
        streak = await _logging_streak(db, user_id)
        for code, need in (("streak_3", 3), ("streak_7", 7), ("streak_30", 30)):
            if streak >= need and not await _has(db, user_id, code):
                await _award(db, user_id, code)
                newly.append(code)

        # veggie hero
        veg = await _veg_count(db, user_id)
        if veg >= 10 and not await _has(db, user_id, "veggie_hero"):
            await _award(db, user_id, "veggie_hero")
            newly.append("veggie_hero")

        # explorer
        distinct = await _distinct_foods(db, user_id)
        if distinct >= 15 and not await _has(db, user_id, "explorer"):
            await _award(db, user_id, "explorer")
            newly.append("explorer")

        # balanced day
        if await _balanced_day(db, user_id, target_calories):
            if not await _has(db, user_id, "balanced_day"):
                await _award(db, user_id, "balanced_day")
                newly.append("balanced_day")

        # hydration streak
        if await _hydration_streak(db, user_id, target_water_ml) >= 3:
            if not await _has(db, user_id, "hydration_pro"):
                await _award(db, user_id, "hydration_pro")
                newly.append("hydration_pro")

        # protein streak
        if await _protein_streak(db, user_id, target_protein_g) >= 5:
            if not await _has(db, user_id, "protein_pro"):
                await _award(db, user_id, "protein_pro")
                newly.append("protein_pro")

        # early logger
        if last_meal is not None and last_meal.meal_type == "breakfast" and last_meal.consumed_at.hour < 9:
            if not await _has(db, user_id, "early_logger"):
                await _award(db, user_id, "early_logger")
                newly.append("early_logger")

        if newly:
            await db.flush()
    except Exception as exc:  # never break the save path on awarder failure
        log.warning("Achievement check failed for user %s: %s", user_id, exc)
        return []

    return newly


def catalog_dict() -> list[dict[str, str]]:
    return [{"code": a.code, "title": a.title, "description": a.description, "icon": a.icon} for a in CATALOG]
