from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from fedwatch.fomc_calendar import FOMCMeeting, meeting_in_month
from fedwatch.probability import days_in_month, solve_implied_rate_after
from fedwatch.probability_mapper import OutcomeDistribution, map_outcomes


@dataclass
class BootstrapNode:
    year: int
    month: int
    futures_price: float
    rate_before: float
    rate_after: float
    meeting: FOMCMeeting | None
    outcomes: OutcomeDistribution | None


def run_bootstrap(
    futures_chain: dict[tuple[int, int], float],
    initial_rate: float,
    start_year_month: tuple[int, int] | None = None,
) -> list[BootstrapNode]:
    sorted_keys = sorted(futures_chain.keys())
    if not sorted_keys:
        return []

    nodes: list[BootstrapNode] = []
    current_rate = initial_rate

    for year, month in sorted_keys:
        price = futures_chain[(year, month)]
        meeting = meeting_in_month(year, month)

        if meeting is not None:
            n_days = days_in_month(year, month)
            days_after = n_days - meeting.decision_date.day

            next_y = year + 1 if month == 12 else year
            next_m = 1 if month == 12 else month + 1
            next_has_meeting = meeting_in_month(next_y, next_m) is not None

            if days_after <= 3 and (next_y, next_m) in futures_chain and not next_has_meeting:
                next_price = futures_chain[(next_y, next_m)]
                rate_after = 100.0 - next_price
            else:
                rate_after = solve_implied_rate_after(
                    futures_price=price,
                    decision_date=meeting.decision_date,
                    current_rate=current_rate,
                )

            outcomes = map_outcomes(rate_before=current_rate, implied_rate_after=rate_after)
            rate_before = current_rate
            current_rate = rate_after
        else:
            rate_before = current_rate
            rate_after = current_rate
            outcomes = None

        nodes.append(
            BootstrapNode(
                year=year,
                month=month,
                futures_price=price,
                rate_before=rate_before,
                rate_after=rate_after,
                meeting=meeting,
                outcomes=outcomes,
            )
        )

    return nodes
