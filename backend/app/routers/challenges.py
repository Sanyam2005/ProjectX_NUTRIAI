from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.deps import DB, CurrentUser
from app.services import challenges as svc

router = APIRouter(prefix="/api/challenges", tags=["challenges"])


@router.get("")
async def list_challenges(user: CurrentUser, db: DB) -> dict[str, Any]:
    items = await svc.list_for_user(db, user.id)
    return {"items": items}


@router.post("/{code}/join")
async def join(code: str, user: CurrentUser, db: DB) -> dict[str, Any]:
    ok = await svc.join(db, user.id, code)
    if not ok:
        raise HTTPException(status_code=404, detail="Unknown challenge")
    await db.commit()
    return {"joined": True, "code": code}


@router.post("/{code}/leave")
async def leave(code: str, user: CurrentUser, db: DB) -> dict[str, Any]:
    ok = await svc.leave(db, user.id, code)
    await db.commit()
    return {"joined": not ok, "code": code}


@router.get("/{code}/leaderboard")
async def leaderboard(code: str, user: CurrentUser, db: DB, limit: int = Query(25, ge=1, le=100)) -> dict[str, Any]:
    return await svc.leaderboard(db, code, current_user_id=user.id, limit=limit)
