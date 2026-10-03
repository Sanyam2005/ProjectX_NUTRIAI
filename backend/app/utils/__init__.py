"""All app timestamps use India Standard Time (UTC+5:30), naive.

NutriAI is built for Microsoft India employees and every "today" / "this week"
calculation has to behave in IST. Database columns stay as naive ``DateTime``
(no tzinfo) so every write goes through ``now_ist()`` and every "what day is
it" read goes through ``today_ist()``. Comparisons then stay consistent no
matter where the server happens to be running.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30), name="IST")


def now_ist() -> datetime:
    """Current IST wall-clock as a naive ``datetime`` (matches DB columns)."""
    return datetime.now(IST).replace(tzinfo=None)


def today_ist() -> date:
    """Today's date in IST."""
    return now_ist().date()
