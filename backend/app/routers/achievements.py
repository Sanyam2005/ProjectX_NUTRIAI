from typing import Any

from fastapi import APIRouter
from sqlalchemy import desc, select

from app.deps import DB, CurrentUser
from app.models import Achievement
from app.services.achievements import CATALOG, catalog_dict

router = APIRouter(prefix="/api/achievements", tags=["achievements"])


@router.get("")
async def list_achievements(user: CurrentUser, db: DB) -> dict[str, Any]:
    rows = (await db.execute(
        select(Achievement).where(Achievement.user_id == user.id).order_by(desc(Achievement.earned_at))
    )).scalars().all()

    earned_codes = {a.code for a in rows}
    earned_by_code = {a.code: a for a in rows}

    items = []
    for defn in CATALOG:
        earned = defn.code in earned_codes
        items.append({
            "code": defn.code,
            "title": defn.title,
            "description": defn.description,
            "icon": defn.icon,
            "earned": earned,
            "earned_at": earned_by_code[defn.code].earned_at.isoformat() if earned else None,
        })

    return {
        "earned_count": len(earned_codes),
        "total": len(CATALOG),
        "items": items,
        "catalog": catalog_dict(),
    }
