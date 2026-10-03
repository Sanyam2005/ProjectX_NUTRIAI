from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.deps import DB, CurrentUser
from app.models import Goal
from app.schemas.goal import GoalIn, GoalOut

router = APIRouter(prefix="/api/goals", tags=["goals"])


@router.get("", response_model=GoalOut)
async def get_goals(user: CurrentUser, db: DB) -> GoalOut:
    goal = (await db.execute(select(Goal).where(Goal.user_id == user.id))).scalar_one_or_none()
    if goal is None:
        goal = Goal(user_id=user.id)
        db.add(goal)
        await db.commit()
        await db.refresh(goal)
    return GoalOut.model_validate(goal)


@router.put("", response_model=GoalOut)
async def update_goals(payload: GoalIn, user: CurrentUser, db: DB) -> GoalOut:
    goal = (await db.execute(select(Goal).where(Goal.user_id == user.id))).scalar_one_or_none()
    if goal is None:
        goal = Goal(user_id=user.id)
        db.add(goal)

    for field, value in payload.model_dump().items():
        setattr(goal, field, value)

    await db.commit()
    await db.refresh(goal)
    return GoalOut.model_validate(goal)


@router.post("/recompute", response_model=GoalOut)
async def recompute_targets(user: CurrentUser, db: DB) -> GoalOut:
    """Estimate target calories from Mifflin-St Jeor + activity multiplier."""
    goal = (await db.execute(select(Goal).where(Goal.user_id == user.id))).scalar_one_or_none()
    if goal is None or not (goal.weight_kg and goal.height_cm and goal.age and goal.gender):
        raise HTTPException(status_code=400, detail="Provide weight, height, age and gender first")

    bmr = 10 * goal.weight_kg + 6.25 * goal.height_cm - 5 * goal.age
    bmr += 5 if goal.gender == "male" else -161

    multiplier = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9,
    }.get(goal.activity_level, 1.55)

    tdee = bmr * multiplier
    target_cal = int(round(tdee / 10) * 10)

    goal.target_calories = target_cal
    goal.target_protein_g = max(int(goal.weight_kg * 1.6), 60)
    goal.target_fat_g = int(target_cal * 0.27 / 9)
    goal.target_carbs_g = int((target_cal - goal.target_protein_g * 4 - goal.target_fat_g * 9) / 4)
    await db.commit()
    await db.refresh(goal)
    return GoalOut.model_validate(goal)
