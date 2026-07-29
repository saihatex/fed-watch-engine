from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Sequence


@dataclass(frozen=True)
class FOMCMeeting:
    start_date: date
    decision_date: date
    has_sep: bool = False


FOMC_MEETINGS_2026 = [
    FOMCMeeting(date(2026, 1, 27), date(2026, 1, 28)),
    FOMCMeeting(date(2026, 3, 17), date(2026, 3, 18), has_sep=True),
    FOMCMeeting(date(2026, 4, 28), date(2026, 4, 29)),
    FOMCMeeting(date(2026, 6, 16), date(2026, 6, 17), has_sep=True),
    FOMCMeeting(date(2026, 7, 28), date(2026, 7, 29)),
    FOMCMeeting(date(2026, 9, 15), date(2026, 9, 16), has_sep=True),
    FOMCMeeting(date(2026, 10, 27), date(2026, 10, 28)),
    FOMCMeeting(date(2026, 12, 8), date(2026, 12, 9), has_sep=True),
]

ALL_MEETINGS = FOMC_MEETINGS_2026

CURRENT_TARGET_RANGE = (3.50, 3.75)
CURRENT_TARGET_MIDPOINT = sum(CURRENT_TARGET_RANGE) / 2
CURRENT_TARGET_SET_DATE = date(2025, 12, 10)


def next_meeting(as_of: date | None = None) -> FOMCMeeting:
    as_of = as_of or date.today()
    upcoming = [m for m in ALL_MEETINGS if m.decision_date >= as_of]
    if not upcoming:
        raise ValueError("No upcoming meeting in calendar — add next year's schedule to fomc_calendar.py")
    return min(upcoming, key=lambda m: m.decision_date)


def meetings_ahead(n: int, as_of: date | None = None) -> list[FOMCMeeting]:
    as_of = as_of or date.today()
    upcoming = sorted(
        [m for m in ALL_MEETINGS if m.decision_date >= as_of],
        key=lambda m: m.decision_date,
    )
    return upcoming[:n]


def meetings_between(start: date, end: date) -> list[FOMCMeeting]:
    return [m for m in ALL_MEETINGS if start <= m.decision_date <= end]


def meeting_in_month(year: int, month: int) -> FOMCMeeting | None:
    for m in ALL_MEETINGS:
        if m.decision_date.year == year and m.decision_date.month == month:
            return m
    return None
