from datetime import datetime
from typing import Any

from fastapi import APIRouter
from sqlalchemy import desc, select
from sqlalchemy.orm import selectinload

from app.deps import DB, CurrentUser
from app.models import Meal
from app.services.recommendations import build_recommendations
from app.services.swaps import suggest_for_names, swap_dict
from app.utils import now_ist

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.get("")
async def recommendations(user: CurrentUser, db: DB) -> dict[str, Any]:
    data = await build_recommendations(db, user.id)

    # Find a swap suggestion against names from the user's last meal (or last
    # few). Fall back to the rolling recent-ingredient list.
    last_meal = (await db.execute(
        select(Meal).options(selectinload(Meal.ingredients))
        .where(Meal.user_id == user.id)
        .order_by(desc(Meal.consumed_at))
        .limit(1)
    )).scalar_one_or_none()

    candidate_names: list[str] = []
    if last_meal is not None:
        candidate_names = [last_meal.name, *[i.name for i in last_meal.ingredients]]
    if not candidate_names:
        candidate_names = data["recent_meal_names"]

    swap = suggest_for_names(candidate_names)
    return {
        "generated_at": now_ist().isoformat(),
        "insights": data["insights"],
        "averages_7d": data["averages_7d"],
        "swap": swap_dict(swap) if swap else None,
    }
