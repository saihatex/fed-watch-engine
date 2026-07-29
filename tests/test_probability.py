from datetime import date

import pytest

from fedwatch.probability import (
    solve_implied_rate_after,
    rate_move_probability,
    days_in_month,
)


def test_days_in_month_september():
    assert days_in_month(2026, 9) == 30


def test_worked_example_matches_72_28():
    current_rate = 5.375
    decision_date = date(2026, 9, 18)
    expected_rate_after = current_rate - 0.72 * 0.25

    n_days = 30
    days_before = 18
    days_after = 12
    avg_rate = (days_before * current_rate + days_after * expected_rate_after) / n_days
    futures_price = 100 - avg_rate

    result = rate_move_probability(futures_price, decision_date, current_rate)

    assert result.direction == "cut"
    assert result.prob_move == pytest.approx(0.72, abs=1e-3)
    assert result.prob_hold == pytest.approx(0.28, abs=1e-3)
    assert result.implied_rate_after == pytest.approx(expected_rate_after, abs=1e-6)


def test_no_move_priced_gives_100pct_hold():
    current_rate = 3.625
    decision_date = date(2026, 7, 29)
    n_days = 31
    days_before = decision_date.day
    days_after = n_days - days_before
    avg_rate = current_rate
    futures_price = 100 - avg_rate

    result = rate_move_probability(futures_price, decision_date, current_rate)

    assert result.direction == "hold"
    assert result.prob_move == pytest.approx(0.0, abs=1e-6)
    assert result.prob_hold == pytest.approx(1.0, abs=1e-6)


def test_hike_direction_detected():
    current_rate = 3.625
    decision_date = date(2026, 4, 29)
    n_days = 30
    days_before = decision_date.day
    days_after = n_days - days_before
    expected_rate_after = current_rate + 0.4 * 0.25
    avg_rate = (days_before * current_rate + days_after * expected_rate_after) / n_days
    futures_price = 100 - avg_rate

    result = rate_move_probability(futures_price, decision_date, current_rate)

    assert result.direction == "hike"
    assert result.prob_move == pytest.approx(0.4, abs=1e-3)


def test_last_day_of_month_raises():
    decision_date = date(2026, 4, 30)
    with pytest.raises(ValueError):
        solve_implied_rate_after(95.0, decision_date, 3.625)


def test_probability_clipped_to_valid_range():
    current_rate = 3.625
    decision_date = date(2026, 6, 17)
    n_days = 30
    days_before = decision_date.day
    days_after = n_days - days_before
    extreme_rate_after = current_rate - 2.0
    avg_rate = (days_before * current_rate + days_after * extreme_rate_after) / n_days
    futures_price = 100 - avg_rate

    result = rate_move_probability(futures_price, decision_date, current_rate)
    assert 0.0 <= result.prob_move <= 1.0
