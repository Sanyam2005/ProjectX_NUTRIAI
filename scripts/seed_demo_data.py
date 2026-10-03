#!/usr/bin/env python
r"""Seed 7 days of demo data for `test@microsoft.com`.

Creates the user (password: ``test1234``) if it doesn't exist, then wipes any
of their existing meals / water / weight / achievement rows for the last
8 days and inserts a realistic Indian-food history so the dashboard rings,
streak, analytics trends, calendar, challenges and achievements all populate
for the demo.

Today (day 0) only gets breakfast + lunch — that way the calorie ring sits at
~50-60 % and visibly moves when you save a new meal during the demo.

Idempotent: safe to re-run.

Run with::

    & .\backend\.venv\Scripts\python.exe .\scripts\seed_demo_data.py
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, time, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
BACKEND = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND))
# Resolve the default SQLite URL (`./nutriai.db`) to backend/nutriai.db so we
# write into the same DB the uvicorn process reads from.
os.chdir(BACKEND)

from sqlalchemy import delete, select  # noqa: E402

from app.data.indian_foods import _FOODS  # noqa: E402
from app.database import SessionLocal, init_db  # noqa: E402
from app.models import (  # noqa: E402
    Achievement,
    Goal,
    Meal,
    MealIngredient,
    User,
    WaterLog,
    WeightHistory,
)
from app.routers.auth import _hash_password  # noqa: E402
from app.services.achievements import check_and_award  # noqa: E402
from app.utils import now_ist  # noqa: E402

# ---- knobs ------------------------------------------------------------------

EMAIL = "test@microsoft.com"
NAME = "Test User"
PASSWORD = "test1234"

GOAL_TARGETS = dict(
    target_calories=2000,
    target_protein_g=85,
    target_carbs_g=240,
    target_fat_g=65,
    target_fiber_g=30,
    target_water_ml=2500,
    weight_kg=72.0,
    target_weight_kg=70.0,
    height_cm=175,
    age=28,
    gender="male",
    activity_level="moderate",
)

CATALOG = {f.name: f for f in _FOODS}

# ---- meal templates ---------------------------------------------------------
# Each day template: (meals, water_logs)
#   meals      : list of (name, type, (hour, min), [(catalog_food, grams), ...])
#   water_logs : list of (hour, amount_ml)
DayTemplate = tuple[
    list[tuple[str, str, tuple[int, int], list[tuple[str, float]]]],
    list[tuple[int, int]],
]


def day_template(offset: int) -> DayTemplate:
    """offset = 6 is six days ago, 0 is today."""
    if offset == 6:  # oldest — calm, balanced
        return ([
            ("Poha breakfast",     "breakfast", (8, 15),  [("Poha", 180), ("Curd", 100)]),
            ("Office thali",       "lunch",     (13, 0),  [("Roti", 80), ("Dal tadka", 150), ("Mixed veg sabzi", 150), ("Curd", 80)]),
            ("Khichdi dinner",     "dinner",    (20, 30), [("Khichdi", 250), ("Curd", 80), ("Pickle (achaar)", 10)]),
        ], [(8, 250), (10, 300), (13, 300), (16, 250), (19, 250), (21, 300)])

    if offset == 5:  # protein-heavy
        return ([
            ("Aloo paratha",       "breakfast", (8, 30),  [("Stuffed paratha", 120), ("Curd", 100)]),
            ("Chole + naan",       "lunch",     (13, 15), [("Chole", 200), ("Naan", 90), ("Mixed salad", 100)]),
            ("Paneer dinner",      "dinner",    (20, 45), [("Roti", 80), ("Paneer butter masala", 150), ("Kachumber salad", 100)]),
        ], [(8, 250), (11, 300), (14, 300), (17, 250), (20, 250), (22, 250)])

    if offset == 4:  # south-Indian
        return ([
            ("Masala dosa",        "breakfast", (8, 45),  [("Masala dosa", 150), ("Sambar", 120), ("Coconut chutney", 30)]),
            ("South thali",        "lunch",     (13, 30), [("Steamed rice", 180), ("Sambar", 180), ("Mixed veg sabzi", 150), ("Curd", 80)]),
            ("Evening snack",      "snack",     (17, 0),  [("Vada", 50), ("Coconut chutney", 30)]),
            ("Idli dinner",        "dinner",    (20, 30), [("Idli", 120), ("Sambar", 180), ("Coconut chutney", 30)]),
        ], [(8, 250), (10, 250), (13, 300), (16, 250), (19, 300), (21, 250)])

    if offset == 3:  # cheat day — slightly over goal
        return ([
            ("Aloo paratha",       "breakfast", (9, 0),   [("Stuffed paratha", 150), ("Curd", 100), ("Pickle (achaar)", 10)]),
            ("Biryani lunch",      "lunch",     (13, 45), [("Biryani (chicken)", 300), ("Raita", 100)]),
            ("Tea + samosa",       "snack",     (17, 30), [("Samosa", 60)]),
            ("Pav bhaji dinner",   "dinner",    (21, 0),  [("Pav bhaji", 200), ("Mixed salad", 80)]),
        ], [(9, 250), (12, 250), (14, 250), (17, 250), (20, 300)])

    if offset == 2:  # balanced
        return ([
            ("Upma breakfast",     "breakfast", (8, 15),  [("Upma", 180), ("Curd", 80)]),
            ("Roti dal sabzi",     "lunch",     (13, 0),  [("Roti", 80), ("Dal makhani", 150), ("Bhindi sabzi", 150), ("Curd", 80)]),
            ("Rajma chawal",       "dinner",    (20, 0),  [("Brown rice", 150), ("Rajma", 150), ("Mixed salad", 100)]),
        ], [(8, 250), (11, 250), (13, 300), (16, 300), (19, 250), (22, 250)])

    if offset == 1:  # yesterday — solid + snack
        return ([
            ("Idli breakfast",     "breakfast", (8, 30),  [("Idli", 105), ("Sambar", 150), ("Coconut chutney", 30)]),
            ("Office lunch",       "lunch",     (13, 15), [("Pulao", 200), ("Palak paneer", 120), ("Raita", 80)]),
            ("Fruit snack",        "snack",     (17, 30), [("Mixed salad", 100)]),
            ("Light dinner",       "dinner",    (20, 30), [("Roti", 80), ("Aloo gobi", 150), ("Dal tadka", 150), ("Curd", 80)]),
        ], [(8, 300), (11, 250), (13, 300), (16, 250), (19, 300), (21, 250)])

    if offset == 0:  # today — only breakfast + lunch (ring stays partial)
        return ([
            ("Poha + chai",        "breakfast", (8, 30),  [("Poha", 180), ("Curd", 80)]),
            ("Quick lunch",        "lunch",     (13, 0),  [("Roti", 80), ("Dal tadka", 150), ("Mixed salad", 100)]),
        ], [(8, 250), (10, 250), (13, 300)])

    return ([], [])


# Slight downward weight trend over the week.
WEIGHT_SERIES = [73.0, 72.8, 72.7, 72.5, 72.3, 72.2, 72.0]  # day -6 → day 0


# ---- helpers ----------------------------------------------------------------

def build_ingredient(catalog_name: str, weight_g: float, position: int) -> MealIngredient:
    f = CATALOG[catalog_name]
    factor = weight_g / 100.0
    return MealIngredient(
        position=position,
        name=f.name,
        weight_g=float(weight_g),
        unit=f.default_unit,
        confidence=0.92,
        calories=round(f.kcal * factor, 1),
        protein_g=round(f.protein_g * factor, 1),
        carbs_g=round(f.carbs_g * factor, 1),
        fat_g=round(f.fat_g * factor, 1),
        fiber_g=round(f.fiber_g * factor, 1),
        sugar_g=round(f.sugar_g * factor, 1),
        sodium_mg=round(f.sodium_mg * factor, 1),
    )


def build_meal(
    user_id: str,
    name: str,
    meal_type: str,
    consumed_at: datetime,
    items: list[tuple[str, float]],
) -> Meal:
    meal = Meal(
        user_id=user_id,
        name=name,
        meal_type=meal_type,
        consumed_at=consumed_at,
        created_at=consumed_at,
    )
    meal.ingredients = [build_ingredient(cn, w, idx) for idx, (cn, w) in enumerate(items)]
    meal.calories  = round(sum(i.calories  for i in meal.ingredients), 1)
    meal.protein_g = round(sum(i.protein_g for i in meal.ingredients), 1)
    meal.carbs_g   = round(sum(i.carbs_g   for i in meal.ingredients), 1)
    meal.fat_g     = round(sum(i.fat_g     for i in meal.ingredients), 1)
    meal.fiber_g   = round(sum(i.fiber_g   for i in meal.ingredients), 1)
    meal.sugar_g   = round(sum(i.sugar_g   for i in meal.ingredients), 1)
    meal.sodium_mg = round(sum(i.sodium_mg for i in meal.ingredients), 1)
    return meal


async def upsert_user(db) -> User:
    user = (await db.execute(select(User).where(User.email == EMAIL))).scalar_one_or_none()
    if user is None:
        user = User(
            email=EMAIL,
            name=NAME,
            is_guest=False,
            password_hash=_hash_password(PASSWORD),
        )
        db.add(user)
        await db.flush()
        print(f"  created user {EMAIL} (password: {PASSWORD})")
    else:
        # Reset the password so we always know the credentials for the demo.
        user.password_hash = _hash_password(PASSWORD)
        user.is_guest = False
        if user.name == "Guest":
            user.name = NAME
        print(f"  found existing user {EMAIL} (password reset to: {PASSWORD})")
    return user


async def upsert_goal(db, user_id: str) -> Goal:
    goal = (await db.execute(select(Goal).where(Goal.user_id == user_id))).scalar_one_or_none()
    if goal is None:
        goal = Goal(user_id=user_id, **GOAL_TARGETS)
        db.add(goal)
    else:
        for k, v in GOAL_TARGETS.items():
            setattr(goal, k, v)
    await db.flush()
    return goal


async def wipe_recent_data(db, user_id: str, days: int = 8) -> None:
    """Delete the user's meals / water / weight / achievements from the last `days` days."""
    cutoff = now_ist() - timedelta(days=days)
    await db.execute(delete(Meal).where(Meal.user_id == user_id, Meal.consumed_at >= cutoff))
    await db.execute(delete(WaterLog).where(WaterLog.user_id == user_id, WaterLog.recorded_at >= cutoff))
    await db.execute(delete(WeightHistory).where(WeightHistory.user_id == user_id, WeightHistory.recorded_at >= cutoff))
    await db.execute(delete(Achievement).where(Achievement.user_id == user_id))
    await db.flush()


async def seed() -> None:
    await init_db()

    today = now_ist().date()
    async with SessionLocal() as db:
        print(f"Seeding demo data for {EMAIL} (today = {today})")
        user = await upsert_user(db)
        goal = await upsert_goal(db, user.id)
        await wipe_recent_data(db, user.id, days=8)

        total_meals = 0
        total_water_ml = 0
        for offset in range(6, -1, -1):  # 6 days ago → today
            day = today - timedelta(days=offset)
            meals_def, water_def = day_template(offset)

            # Meals
            last_meal: Meal | None = None
            for name, mtype, (hh, mm), items in meals_def:
                consumed = datetime.combine(day, time(hh, mm))
                meal = build_meal(user.id, name, mtype, consumed, items)
                db.add(meal)
                last_meal = meal
                total_meals += 1

            # Water
            for hh, ml in water_def:
                db.add(WaterLog(
                    user_id=user.id,
                    amount_ml=ml,
                    recorded_at=datetime.combine(day, time(hh, 0)),
                ))
                total_water_ml += ml

            # Weight (one per day)
            weight = WEIGHT_SERIES[6 - offset]
            db.add(WeightHistory(
                user_id=user.id,
                weight_kg=weight,
                recorded_at=datetime.combine(day, time(7, 30)),
            ))

            await db.flush()

            # Achievements — pass the last meal of the day so the streak/balanced
            # checks see today's totals. Best-effort; failures are swallowed.
            if last_meal is not None:
                await check_and_award(
                    db,
                    user.id,
                    target_calories=goal.target_calories,
                    target_protein_g=goal.target_protein_g,
                    target_water_ml=goal.target_water_ml,
                    last_meal=last_meal,
                )

        await db.commit()

        # Summary
        meals_in_db = (await db.execute(
            select(Meal).where(Meal.user_id == user.id).order_by(Meal.consumed_at)
        )).scalars().all()
        achievements = (await db.execute(
            select(Achievement).where(Achievement.user_id == user.id)
        )).scalars().all()

        print()
        print(f"  Meals seeded         : {total_meals}")
        print(f"  Water logs seeded    : {len(meals_def) and total_water_ml or total_water_ml} ml across 7 days")
        print(f"  Weight history       : 7 entries (73.0 -> 72.0 kg)")
        print(f"  Achievements earned  : {len(achievements)}  ({', '.join(a.code for a in achievements) or '-'})")
        print(f"  Meals now in DB      : {len(meals_in_db)}")
        print()
        print(f"  Sign in at /login    : email={EMAIL}  password={PASSWORD}")


if __name__ == "__main__":
    asyncio.run(seed())
