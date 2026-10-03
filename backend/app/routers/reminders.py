import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select

from app.deps import DB, CurrentUser
from app.models import ReminderSettings

router = APIRouter(prefix="/api/reminders", tags=["reminders"])

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


class ReminderIn(BaseModel):
    breakfast_enabled: bool = True
    breakfast_time: str = Field(default="08:30")
    lunch_enabled: bool = True
    lunch_time: str = Field(default="13:00")
    dinner_enabled: bool = True
    dinner_time: str = Field(default="20:00")
    water_enabled: bool = True
    water_every_min: int = Field(default=120, ge=15, le=480)
    log_enabled: bool = True
    log_time: str = Field(default="21:30")

    @field_validator("breakfast_time", "lunch_time", "dinner_time", "log_time")
    @classmethod
    def _valid_hhmm(cls, v: str) -> str:
        if not _TIME_RE.match(v):
            raise ValueError("time must be HH:MM (24h)")
        return v


class ReminderOut(ReminderIn):
    pass


async def _get_or_create(db, user_id: str) -> ReminderSettings:
    res = await db.execute(select(ReminderSettings).where(ReminderSettings.user_id == user_id))
    row = res.scalar_one_or_none()
    if row is None:
        row = ReminderSettings(user_id=user_id)
        db.add(row)
        await db.commit()
        await db.refresh(row)
    return row


@router.get("", response_model=ReminderOut)
async def get_reminders(user: CurrentUser, db: DB) -> ReminderOut:
    row = await _get_or_create(db, user.id)
    return ReminderOut(
        breakfast_enabled=row.breakfast_enabled, breakfast_time=row.breakfast_time,
        lunch_enabled=row.lunch_enabled,         lunch_time=row.lunch_time,
        dinner_enabled=row.dinner_enabled,       dinner_time=row.dinner_time,
        water_enabled=row.water_enabled,         water_every_min=row.water_every_min,
        log_enabled=row.log_enabled,             log_time=row.log_time,
    )


@router.put("", response_model=ReminderOut)
async def update_reminders(payload: ReminderIn, user: CurrentUser, db: DB) -> ReminderOut:
    row = await _get_or_create(db, user.id)
    for k, v in payload.model_dump().items():
        setattr(row, k, v)
    await db.commit()
    await db.refresh(row)
    return ReminderOut(**payload.model_dump())
