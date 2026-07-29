from datetime import date
from fedwatch.bias_engine import analyze_macro_bias
from fedwatch.bootstrap import BootstrapNode
from fedwatch.news_loader import EconomicEvent
from fedwatch.probability_mapper import OutcomeDistribution


def test_bias_engine_hawkish():
    nodes = [
        BootstrapNode(
            year=2026,
            month=7,
            futures_price=96.35,
            rate_before=3.625,
            rate_after=3.875,
            meeting=None,
            outcomes=OutcomeDistribution(rate_before=3.625, implied_rate_after=3.875, probs={25: 1.0}),
        )
    ]
    events = [
        EconomicEvent(
            event_id="cpi_1",
            event_date=date.today(),
            event_time="13:30",
            currency="USD",
            event_name="Core CPI (MoM)",
            impact="High",
            forecast=0.3,
            actual=0.5,
        )
    ]

    bias = analyze_macro_bias(nodes, events)
    assert "HAWKISH" in bias.overall_bias
    assert len(bias.smc_playbook) >= 2
