from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import and_, delete, desc, func, select
from sqlalchemy.orm import selectinload

from app.deps import DB, CurrentUser
from app.models import Goal, Meal, MealIngredient
from app.schemas.meal import MealCreate, MealOut, MealUpdate
from app.services.achievements import check_and_award
from app.utils import now_ist

router = APIRouter(prefix="/api/meals", tags=["meals"])


def _totals(ingredients) -> dict[str, float]:
    keys = ("calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "sugar_g", "sodium_mg")
    return {k: round(sum(getattr(i, k, 0) or 0 for i in ingredients), 1) for k in keys}


@router.post("", response_model=MealOut, status_code=status.HTTP_201_CREATED)
async def create_meal(payload: MealCreate, user: CurrentUser, db: DB) -> MealOut:
    meal = Meal(
        user_id=user.id,
        name=payload.name,
        meal_type=payload.meal_type,
        image_url=payload.image_url,
        notes=payload.notes,
        consumed_at=payload.consumed_at or now_ist(),
    )
    for idx, ing in enumerate(payload.ingredients):
        meal.ingredients.append(MealIngredient(position=idx, **ing.model_dump()))

    totals = _totals(meal.ingredients)
    for k, v in totals.items():
        setattr(meal, k, v)

    db.add(meal)
    await db.flush()

    # Award any newly-earned achievements before committing so they go in the
    # same transaction. Best-effort: awarder swallows its own errors.
    goal = (await db.execute(select(Goal).where(Goal.user_id == user.id))).scalar_one_or_none()
    await check_and_award(
        db,
        user.id,
        target_calories=goal.target_calories if goal else 2000,
        target_protein_g=goal.target_protein_g if goal else 80,
        target_water_ml=goal.target_water_ml if goal else 2500,
        last_meal=meal,
    )

    await db.commit()

    refreshed = await db.execute(
        select(Meal).options(selectinload(Meal.ingredients)).where(Meal.id == meal.id)
    )
    return MealOut.model_validate(refreshed.scalar_one())


@router.get("", response_model=list[MealOut])
async def list_meals(
    user: CurrentUser,
    db: DB,
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"] | None = None,
    q: str | None = Query(default=None, description="search in meal name"),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[MealOut]:
    stmt = (
        select(Meal)
        .options(selectinload(Meal.ingredients))
        .where(Meal.user_id == user.id)
        .order_by(desc(Meal.consumed_at))
        .limit(limit)
        .offset(offset)
    )
    conds = []
    if meal_type:
        conds.append(Meal.meal_type == meal_type)
    if q:
        conds.append(func.lower(Meal.name).contains(q.lower()))
    if date_from:
        conds.append(Meal.consumed_at >= date_from)
    if date_to:
        conds.append(Meal.consumed_at <= date_to)
    if conds:
        stmt = stmt.where(and_(*conds))

    result = await db.execute(stmt)
    return [MealOut.model_validate(m) for m in result.scalars().all()]


async def _get_meal(meal_id: str, user_id: str, db) -> Meal:
    result = await db.execute(
        select(Meal)
        .options(selectinload(Meal.ingredients))
        .where(Meal.id == meal_id, Meal.user_id == user_id)
    )
    meal = result.scalar_one_or_none()
    if meal is None:
        raise HTTPException(status_code=404, detail="Meal not found")
    return meal


@router.get("/{meal_id}", response_model=MealOut)
async def get_meal(meal_id: str, user: CurrentUser, db: DB) -> MealOut:
    return MealOut.model_validate(await _get_meal(meal_id, user.id, db))


@router.put("/{meal_id}", response_model=MealOut)
async def update_meal(meal_id: str, payload: MealUpdate, user: CurrentUser, db: DB) -> MealOut:
    meal = await _get_meal(meal_id, user.id, db)

    if payload.name is not None:
        meal.name = payload.name
    if payload.meal_type is not None:
        meal.meal_type = payload.meal_type
    if payload.notes is not None:
        meal.notes = payload.notes
    if payload.consumed_at is not None:
        meal.consumed_at = payload.consumed_at

    if payload.ingredients is not None:
        # Replace ingredient list — simpler and matches the editable UI model.
        await db.execute(delete(MealIngredient).where(MealIngredient.meal_id == meal.id))
        await db.flush()
        meal.ingredients = [
            MealIngredient(position=idx, **ing.model_dump())
            for idx, ing in enumerate(payload.ingredients)
        ]
        totals = _totals(meal.ingredients)
        for k, v in totals.items():
            setattr(meal, k, v)

    await db.commit()
    refreshed = await db.execute(
        select(Meal).options(selectinload(Meal.ingredients)).where(Meal.id == meal.id)
    )
    return MealOut.model_validate(refreshed.scalar_one())


@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal(meal_id: str, user: CurrentUser, db: DB) -> None:
    meal = await _get_meal(meal_id, user.id, db)
    await db.delete(meal)
    await db.commit()
