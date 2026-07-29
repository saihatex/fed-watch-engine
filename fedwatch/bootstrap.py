from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from fedwatch.fomc_calendar import FOMCMeeting, meeting_in_month
from fedwatch.probability import solve_implied_rate_after
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
