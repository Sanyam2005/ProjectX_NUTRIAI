from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils import now_ist


def _uuid() -> str:
    return str(uuid.uuid4())


class ChallengeParticipant(Base):
    """Opt-in record: a user has joined the given challenge code.

    Challenges themselves are defined in code (see
    ``app.services.challenges``) so the catalog can evolve without DB
    migrations. Progress and leaderboards are computed on the fly from the
    user's meals + water logs.
    """
    __tablename__ = "challenge_participants"
    __table_args__ = (UniqueConstraint("user_id", "challenge_code", name="uq_participant_user_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    challenge_code: Mapped[str] = mapped_column(String(64), index=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=now_ist)
