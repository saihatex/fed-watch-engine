from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import calendar


@dataclass
class RateExpectation:
    meeting_decision_date: date
    current_rate: float
    implied_rate_after: float
    step_size: float
    prob_move: float
    prob_hold: float
    direction: str

    def __str__(self) -> str:
        pct = lambda x: f"{x * 100:.0f}%"
        if self.direction == "hold":
            return f"FOMC {self.meeting_decision_date}: ~{pct(self.prob_hold)} no change"
        return (
            f"FOMC {self.meeting_decision_date}: "
            f"{int(round(self.step_size * 100))}bp {self.direction}: {pct(self.prob_move)}  |  "
            f"no change: {pct(self.prob_hold)}"
        )


def implied_average_rate(futures_price: float) -> float:
    return 100.0 - futures_price


def days_in_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def solve_implied_rate_after(
    futures_price: float,
    decision_date: date,
    current_rate: float,
) -> float:
    n_days = days_in_month(decision_date.year, decision_date.month)
    days_before = decision_date.day
    days_after = n_days - days_before

    if days_after <= 0:
        raise ValueError(
            "Decision date falls on the last day of the month — use the next contract month instead"
        )

    avg_rate = implied_average_rate(futures_price)
    return (n_days * avg_rate - days_before * current_rate) / days_after


def rate_move_probability(
    futures_price: float,
    decision_date: date,
    current_rate: float,
    step_size: float = 0.25,
) -> RateExpectation:
    rate_after = solve_implied_rate_after(futures_price, decision_date, current_rate)
    delta = current_rate - rate_after

    prob_move = max(0.0, min(1.0, abs(delta) / step_size))
    prob_hold = 1 - prob_move

    if prob_move < 0.005:
        direction = "hold"
    elif delta > 0:
        direction = "cut"
    else:
        direction = "hike"

    return RateExpectation(
        meeting_decision_date=decision_date,
        current_rate=current_rate,
        implied_rate_after=rate_after,
        step_size=step_size,
        prob_move=prob_move,
        prob_hold=prob_hold,
        direction=direction,
    )


def compare_to_previous(
    today: RateExpectation,
    previous: RateExpectation,
) -> float:
    return today.prob_move - previous.prob_move
