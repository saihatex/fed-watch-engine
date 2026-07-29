from datetime import date
import pytest

from fedwatch.bootstrap import run_bootstrap
from fedwatch.probability_mapper import map_outcomes


def test_map_outcomes_hold():
    res = map_outcomes(rate_before=3.625, implied_rate_after=3.625)
    assert res.probs[0] == pytest.approx(1.0)


def test_map_outcomes_25bp_cut():
    res = map_outcomes(rate_before=3.625, implied_rate_after=3.375)
    assert res.probs[-25] == pytest.approx(1.0)
    assert res.probs[0] == pytest.approx(0.0)


def test_map_outcomes_partial_cut():
    res = map_outcomes(rate_before=3.625, implied_rate_after=3.50)
    # 0.125 / 0.25 = 50% cut, 50% hold
    assert res.probs[-25] == pytest.approx(0.5)
    assert res.probs[0] == pytest.approx(0.5)


def test_bootstrap_multi_month():
    # 2026-07 meeting (month 7), 2026-09 meeting (month 9)
    chain = {
        (2026, 7): 96.25,
        (2026, 8): 96.25,
        (2026, 9): 96.40,
    }
    nodes = run_bootstrap(futures_chain=chain, initial_rate=3.625)
    assert len(nodes) == 3
    assert nodes[0].meeting is not None
    assert nodes[1].meeting is None
    assert nodes[2].meeting is not None
