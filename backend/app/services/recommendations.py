"""Personalised insight engine.

Walks the user's recent meals, goals, and body metrics, then runs a set of
small rules — each emits at most one short, actionable insight. The top 5
are ranked by priority so the most-urgent advice surfaces first, and what
the user sees changes as their data changes (no canned daily tips).

Designed to be deterministic and fast (one batched DB read + pure-Python
rule evaluation) so it can be called on every dashboard load.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Goal, Meal, MealIngredient, WaterLog, WeightHistory
from app.utils import now_ist, today_ist


_VEG_KEYWORDS = {
    "salad", "veg", "vegetable", "spinach", "palak", "broccoli", "cauliflower", "gobi",
    "carrot", "tomato", "cucumber", "lettuce", "kale", "cabbage", "peas", "matar",
    "beans", "bhindi", "okra", "lauki", "karela", "tinda", "baingan", "brinjal",
    "methi", "fenugreek", "onion", "capsicum", "mushroom", "kachumber", "raita",
}

_SUGGESTED_DINNERS = [
    "Try dal + roti + a bowl of sabzi tonight — balanced and ~550 kcal.",
    "Tonight: grilled paneer with a big salad — high protein, low carb.",
    "Khichdi + curd is light, gut-friendly, ~450 kcal — good after a heavy lunch.",
    "Palak paneer + 1 roti + cucumber raita keeps fat in check.",
    "Veg pulao + raita + a small kachumber — under 600 kcal and filling.",
]

_ACTIVITY_MULTIPLIER = {
    "sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725, "very_active": 1.9,
}


def _is_veg(name: str) -> bool:
    low = name.lower()
    return any(k in low for k in _VEG_KEYWORDS)


def _bmr_mifflin(weight_kg: float, height_cm: float, age: int, gender: str | None) -> float:
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    g = (gender or "").lower()
    if g == "male":
        return base + 5
    if g == "female":
        return base - 161
    return base - 78  # midpoint when gender unspecified


# ---------- Snapshot --------------------------------------------------------

@dataclass
class Snapshot:
    """Pre-computed view of the user's recent state. Rules read only from this."""

    user_id: str

    target_cal: float = 2000
    target_protein: float = 80
    target_carbs: float = 250
    target_fat: float = 65
    target_fiber: float = 30
    target_water: float = 2500

    weight_kg: float | None = None
    target_weight_kg: float | None = None
    height_cm: float | None = None
    age: int | None = None
    gender: str | None = None
    activity_level: str = "moderate"

    bmr: float | None = None
    tdee: float | None = None
    weight_trend_kg_per_wk: float | None = None  # +ve = gaining

    avg_7d: dict[str, float] = field(default_factory=dict)
    day_kcal_by_meal_type: dict[date, dict[str, float]] = field(default_factory=dict)

    today_kcal: float = 0
    today_protein: float = 0
    today_carbs: float = 0
    today_fat: float = 0
    today_fiber: float = 0
    today_sodium: float = 0
    today_water_ml: float = 0
    today_veg_count: int = 0
    today_meal_count: int = 0

    streak: int = 0
    recent_meal_names: list[str] = field(default_factory=list)
    hour_ist: int = 12
    weekday_ist: int = 0

    @property
    def is_cutting(self) -> bool:
        return bool(
            self.target_weight_kg is not None
            and self.weight_kg is not None
            and self.target_weight_kg < self.weight_kg - 1
        )

    @property
    def is_bulking(self) -> bool:
        return bool(
            self.target_weight_kg is not None
            and self.weight_kg is not None
            and self.target_weight_kg > self.weight_kg + 1
        )


async def _build_snapshot(db: AsyncSession, user_id: str) -> Snapshot:
    s = Snapshot(user_id=user_id)
    now = now_ist()
    today = today_ist()
    s.hour_ist = now.hour
    s.weekday_ist = now.weekday()

    # Goal + body metrics
    goal = (await db.execute(select(Goal).where(Goal.user_id == user_id))).scalar_one_or_none()
    if goal is not None:
        s.target_cal = goal.target_calories
        s.target_protein = goal.target_protein_g
        s.target_carbs = goal.target_carbs_g
        s.target_fat = goal.target_fat_g
        s.target_fiber = goal.target_fiber_g
        s.target_water = goal.target_water_ml
        s.weight_kg = goal.weight_kg
        s.target_weight_kg = goal.target_weight_kg
        s.height_cm = goal.height_cm
        s.age = goal.age
        s.gender = goal.gender
        s.activity_level = goal.activity_level or "moderate"

    if s.weight_kg and s.height_cm and s.age and s.age > 0:
        s.bmr = _bmr_mifflin(s.weight_kg, s.height_cm, s.age, s.gender)
        s.tdee = s.bmr * _ACTIVITY_MULTIPLIER.get(s.activity_level, 1.55)

    # One batched read of the last 14 days of meals
    start14 = datetime.combine(today - timedelta(days=13), time.min)
    meals = (await db.execute(
        select(Meal).where(Meal.user_id == user_id, Meal.consumed_at >= start14)
    )).scalars().all()

    day_totals: dict[date, dict[str, float]] = {}
    day_mt: dict[date, dict[str, float]] = {}
    for m in meals:
        d = m.consumed_at.date()
        bucket = day_totals.setdefault(
            d,
            {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0, "fiber_g": 0.0, "sodium_mg": 0.0},
        )
        bucket["calories"]  += m.calories  or 0
        bucket["protein_g"] += m.protein_g or 0
        bucket["carbs_g"]   += m.carbs_g   or 0
        bucket["fat_g"]     += m.fat_g     or 0
        bucket["fiber_g"]   += m.fiber_g   or 0
        bucket["sodium_mg"] += m.sodium_mg or 0
        mt = day_mt.setdefault(d, {})
        mt[m.meal_type] = mt.get(m.meal_type, 0.0) + (m.calories or 0)
    s.day_kcal_by_meal_type = day_mt

    start7 = today - timedelta(days=6)
    avg = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0, "fiber_g": 0.0, "sodium_mg": 0.0}
    for i in range(7):
        v = day_totals.get(start7 + timedelta(days=i))
        if v:
            for k in avg:
                avg[k] += v.get(k, 0.0)
    for k in avg:
        avg[k] /= 7
    s.avg_7d = avg

    today_bucket = day_totals.get(today, {})
    s.today_kcal    = today_bucket.get("calories",  0.0)
    s.today_protein = today_bucket.get("protein_g", 0.0)
    s.today_carbs   = today_bucket.get("carbs_g",   0.0)
    s.today_fat     = today_bucket.get("fat_g",     0.0)
    s.today_fiber   = today_bucket.get("fiber_g",   0.0)
    s.today_sodium  = today_bucket.get("sodium_mg", 0.0)
    s.today_meal_count = sum(1 for m in meals if m.consumed_at.date() == today)

    start_today = datetime.combine(today, time.min)
    end_today = datetime.combine(today, time.max)
    s.today_water_ml = float((await db.execute(
        select(func.coalesce(func.sum(WaterLog.amount_ml), 0))
        .where(WaterLog.user_id == user_id, WaterLog.recorded_at >= start_today, WaterLog.recorded_at <= end_today)
    )).scalar_one() or 0)

    veg_names = (await db.execute(
        select(MealIngredient.name)
        .join(Meal, Meal.id == MealIngredient.meal_id)
        .where(Meal.user_id == user_id, Meal.consumed_at >= start_today, Meal.consumed_at <= end_today)
    )).scalars().all()
    s.today_veg_count = sum(1 for n in veg_names if _is_veg(n))

    start2 = datetime.combine(today - timedelta(days=1), time.min)
    s.recent_meal_names = list((await db.execute(
        select(MealIngredient.name)
        .join(Meal, Meal.id == MealIngredient.meal_id)
        .where(Meal.user_id == user_id, Meal.consumed_at >= start2)
        .order_by(desc(Meal.consumed_at))
        .limit(40)
    )).scalars().all())

    logged_days = set(day_totals.keys())
    streak = 0
    cursor = today
    while cursor in logged_days:
        streak += 1
        cursor -= timedelta(days=1)
    s.streak = streak

    start28 = datetime.combine(today - timedelta(days=27), time.min)
    weight_rows = (await db.execute(
        select(WeightHistory.recorded_at, WeightHistory.weight_kg)
        .where(WeightHistory.user_id == user_id, WeightHistory.recorded_at >= start28)
        .order_by(WeightHistory.recorded_at)
    )).all()
    if len(weight_rows) >= 2:
        first_t, first_w = weight_rows[0]
        last_t, last_w = weight_rows[-1]
        span_days = max((last_t - first_t).total_seconds() / 86400, 1)
        s.weight_trend_kg_per_wk = (float(last_w) - float(first_w)) * 7 / span_days

    return s


# ---------- Insight + rule registry ----------------------------------------

@dataclass
class Insight:
    code: str
    tone: str
    icon: str
    title: str
    body: str
    priority: int  # higher = surfaces first

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "tone": self.tone, "icon": self.icon, "title": self.title, "body": self.body}


def _r_morning_no_log(s: Snapshot) -> Insight | None:
    if not (7 <= s.hour_ist < 11) or s.today_meal_count > 0:
        return None
    return Insight("morning_breakfast", "timing", "🌅", "Good morning",
                   "Log breakfast to start the day. A solid breakfast usually keeps lunch lighter.", 85)


def _r_weight_trend(s: Snapshot) -> Insight | None:
    if s.weight_trend_kg_per_wk is None or s.weight_kg is None or s.target_weight_kg is None:
        return None
    rate = s.weight_trend_kg_per_wk
    diff = s.target_weight_kg - s.weight_kg
    if diff < -1 and rate > 0.1:
        return Insight("weight_trend_off_cut", "weight", "📉", "Trending up while cutting",
                       f"You're +{rate:.1f} kg/wk while aiming to lose. Trim ~200 kcal/day or add 20 min of brisk walking.", 80)
    if diff > 1 and rate < -0.1:
        return Insight("weight_trend_off_bulk", "weight", "📈", "Trending down while bulking",
                       f"You're {rate:+.1f} kg/wk but trying to gain. Add a snack or +200 kcal at dinner.", 80)
    if diff < -1 and rate < -0.05:
        return Insight("weight_trend_on_track", "momentum", "✅", "On track",
                       f"Down {abs(rate):.1f} kg/wk — exactly the cut you wanted. Keep the routine.", 50)
    return None


def _r_tdee_mismatch(s: Snapshot) -> Insight | None:
    if s.tdee is None:
        return None
    if s.is_cutting:
        ideal = s.tdee * 0.80
    elif s.is_bulking:
        ideal = s.tdee * 1.10
    else:
        ideal = s.tdee
    if ideal <= 0 or abs(s.target_cal - ideal) / ideal <= 0.25:
        return None
    return Insight("tdee_mismatch", "calories", "🎯", "Your kcal goal looks off",
                   f"Based on your weight/height/age and activity, ~{int(ideal)} kcal/day fits your weight goal. Hit Auto on Goals to recalculate.", 70)


def _r_midday_low_protein(s: Snapshot) -> Insight | None:
    if not (14 <= s.hour_ist < 18) or s.today_protein >= s.target_protein * 0.4:
        return None
    gap = round(s.target_protein - s.today_protein)
    return Insight("midday_low_protein", "protein", "💪", "Protein running low today",
                   f"{round(s.today_protein)} g logged so far — about {gap} g to go. A boiled egg, paneer cube tray or curd snack works.", 75)


def _r_late_hydration(s: Snapshot) -> Insight | None:
    if s.hour_ist < 20 or s.today_water_ml >= s.target_water * 0.7:
        return None
    remaining = max(int(s.target_water - s.today_water_ml), 0)
    return Insight("late_hydration", "water", "💧", "Last call for hydration",
                   f"{int(s.today_water_ml)} ml so far — {remaining} ml to your daily goal.", 75)


def _r_today_sodium(s: Snapshot) -> Insight | None:
    if s.today_sodium <= 1500 or s.hour_ist >= 19:
        return None
    return Insight("today_sodium", "sodium", "🧂", "Sodium already high today",
                   f"{int(s.today_sodium)} mg by mid-day — go easy on pickles, papad and packaged snacks at dinner.", 72)


def _r_evening_underfueled(s: Snapshot) -> Insight | None:
    if s.hour_ist < 18 or s.hour_ist >= 22 or s.is_cutting or s.today_kcal >= s.target_cal * 0.65:
        return None
    remaining = max(int(s.target_cal - s.today_kcal), 0)
    return Insight("evening_underfueled", "calories", "🍱", "Still under for the day",
                   f"You have ~{remaining} kcal left. Dal + roti + sabzi or a paneer wrap fits the gap.", 65)


def _r_protein_gap(s: Snapshot) -> Insight | None:
    if s.avg_7d["protein_g"] >= s.target_protein * 0.8:
        return None
    gap = round(s.target_protein - s.avg_7d["protein_g"])
    return Insight("protein_gap_7d", "protein", "💪", "Bump up protein",
                   f"Averaging {round(s.avg_7d['protein_g'])} g/day — about {gap} g short. Add an egg, paneer or dal at one meal.", 55)


def _r_fiber_gap(s: Snapshot) -> Insight | None:
    if s.avg_7d["fiber_g"] >= s.target_fiber * 0.7:
        return None
    return Insight("fiber_gap_7d", "fiber", "🌿", "More fiber, fewer dips",
                   f"Averaging {round(s.avg_7d['fiber_g'])} g fiber/day. Swap white rice for brown or add a salad to lunch.", 50)


def _r_sodium_high_7d(s: Snapshot) -> Insight | None:
    if s.avg_7d["sodium_mg"] <= 2300:
        return None
    return Insight("sodium_high_7d", "sodium", "🧂", "Watch the sodium",
                   f"~{round(s.avg_7d['sodium_mg'])} mg/day on average — pickles, papad and packaged snacks add up fast.", 45)


def _r_macro_drift(s: Snapshot) -> Insight | None:
    total = s.avg_7d["calories"]
    if total < 500:
        return None
    actual = {
        "protein": s.avg_7d["protein_g"] * 4 / total * 100,
        "carbs":   s.avg_7d["carbs_g"]   * 4 / total * 100,
        "fat":     s.avg_7d["fat_g"]     * 9 / total * 100,
    }
    goal_total = s.target_protein * 4 + s.target_carbs * 4 + s.target_fat * 9
    if goal_total <= 0:
        return None
    goal_pct = {
        "protein": s.target_protein * 4 / goal_total * 100,
        "carbs":   s.target_carbs   * 4 / goal_total * 100,
        "fat":     s.target_fat     * 9 / goal_total * 100,
    }
    diffs = {k: actual[k] - goal_pct[k] for k in actual}
    name, delta = max(diffs.items(), key=lambda kv: abs(kv[1]))
    if abs(delta) < 15:
        return None
    if delta > 0:
        msg = {
            "protein": "You're protein-heavy lately — fine if it fits, but balance with veggies.",
            "carbs":   "Carbs are running well over your target. One rice/roti swap per day usually closes it.",
            "fat":     "Fat is high — go easy on ghee/oil and butter-based curries this week.",
        }[name]
    else:
        msg = {
            "protein": "Protein share is well below target — add one paneer/egg/dal portion per day.",
            "carbs":   "Carbs are running below target — your energy may dip in the afternoon.",
            "fat":     "Fat is running low — a handful of nuts or 1 tbsp ghee adds healthy fats.",
        }[name]
    return Insight(f"macro_drift_{name}", name, "⚖️", f"{name.capitalize()} mix is off", msg, 60)


def _r_dinner_heavy(s: Snapshot) -> Insight | None:
    eligible = [d for d, mt in s.day_kcal_by_meal_type.items() if mt and sum(mt.values()) > 500]
    if len(eligible) < 4:
        return None
    ratios = []
    for d in eligible:
        total = sum(s.day_kcal_by_meal_type[d].values()) or 1
        dinner = s.day_kcal_by_meal_type[d].get("dinner", 0)
        ratios.append(dinner / total)
    if not ratios:
        return None
    avg_ratio = sum(ratios) / len(ratios)
    if avg_ratio < 0.45:
        return None
    return Insight("dinner_heavy", "timing", "🌙", "Dinner is your biggest meal",
                   f"On average dinner is {int(avg_ratio * 100)}% of the day's calories. Lighter dinners help sleep and recovery — try khichdi or a soup + roti.", 55)


def _r_breakfast_skip(s: Snapshot) -> Insight | None:
    last7 = [today_ist() - timedelta(days=i) for i in range(7)]
    logged = sum(1 for d in last7 if (s.day_kcal_by_meal_type.get(d) or {}).get("breakfast", 0) > 50)
    if logged > 3:
        return None
    return Insight("breakfast_skip", "timing", "🍳", "Breakfast often skipped",
                   f"Logged breakfast on {logged} of the last 7 days. Even a quick poha or 2 eggs evens out lunch hunger.", 48)


def _r_calories_over(s: Snapshot) -> Insight | None:
    if s.avg_7d["calories"] <= s.target_cal * 1.1:
        return None
    over = round(s.avg_7d["calories"] - s.target_cal)
    return Insight("calories_over_7d", "calories", "🔥", "Slightly over budget",
                   f"Avg {round(s.avg_7d['calories'])} kcal/day — about {over} over goal. One swap a day usually closes the gap.", 52)


def _r_calories_under(s: Snapshot) -> Insight | None:
    avg = s.avg_7d["calories"]
    if not (0 < avg < s.target_cal * 0.75) or s.is_cutting:
        return None
    return Insight("calories_under_7d", "calories", "🍱", "Eat a little more",
                   f"Avg {round(avg)} kcal/day — that's under your target. Underfueling slows recovery.", 50)


def _r_today_veg(s: Snapshot) -> Insight | None:
    if s.today_veg_count >= 1 or s.hour_ist < 14:
        return None
    return Insight("today_veg_missing", "veggies", "🥗", "Add some greens today",
                   "No vegetables in today's log yet — a salad, raita, or any sabzi counts.", 58)


def _r_streak_milestone(s: Snapshot) -> Insight | None:
    targets = {2: "On a Roll (3 days)", 6: "Streak Star (7 days)", 13: "two-week streak", 29: "Habit Built (30 days)"}
    if s.streak not in targets:
        return None
    return Insight("streak_milestone", "momentum", "🔥", f"Day {s.streak} — one more for {targets[s.streak]}",
                   f"Log a meal tomorrow to unlock '{targets[s.streak]}'.", 45)


def _r_dinner_suggestion(s: Snapshot) -> Insight | None:
    if s.hour_ist < 17 or s.hour_ist >= 21:
        return None
    seed = sum(ord(c) for c in s.user_id) + today_ist().toordinal()
    return Insight("dinner_suggestion", "suggestion", "🍽️", "Tonight's suggestion",
                   _SUGGESTED_DINNERS[seed % len(_SUGGESTED_DINNERS)], 30)


_RULES = [
    _r_morning_no_log,
    _r_weight_trend,
    _r_tdee_mismatch,
    _r_midday_low_protein,
    _r_late_hydration,
    _r_today_sodium,
    _r_evening_underfueled,
    _r_macro_drift,
    _r_today_veg,
    _r_dinner_heavy,
    _r_protein_gap,
    _r_calories_over,
    _r_calories_under,
    _r_fiber_gap,
    _r_breakfast_skip,
    _r_sodium_high_7d,
    _r_streak_milestone,
    _r_dinner_suggestion,
]


async def build_recommendations(db: AsyncSession, user_id: str) -> dict:
    s = await _build_snapshot(db, user_id)

    insights: list[Insight] = []
    for rule in _RULES:
        try:
            ins = rule(s)
        except Exception:
            ins = None
        if ins is not None:
            insights.append(ins)

    insights.sort(key=lambda i: i.priority, reverse=True)

    # Dedupe by tone so we don't show two protein insights at once; preserve order.
    seen: set[str] = set()
    deduped: list[Insight] = []
    for ins in insights:
        if ins.tone in seen:
            continue
        seen.add(ins.tone)
        deduped.append(ins)

    return {
        "insights": [i.to_dict() for i in deduped[:5]],
        "recent_meal_names": s.recent_meal_names,
        "averages_7d": {k: round(v, 1) for k, v in s.avg_7d.items()},
    }

