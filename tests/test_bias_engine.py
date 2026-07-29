from datetime import date
from fedwatch.bias_engine import analyze_sentiment, SentimentIndex
from fedwatch.bootstrap import BootstrapNode
from fedwatch.news_loader import EconomicEvent
from fedwatch.probability_mapper import OutcomeDistribution


def test_sentiment_hawkish():
    nodes = [
        BootstrapNode(
            year=2026, month=7, futures_price=96.35,
            rate_before=3.625, rate_after=3.875, meeting=None,
            outcomes=OutcomeDistribution(rate_before=3.625, implied_rate_after=3.875, probs={25: 1.0}),
        )
    ]
    events = [
        EconomicEvent(
            event_id="cpi_1", event_date=date.today(), event_time="13:30",
            currency="USD", event_name="Core CPI (MoM)", impact="High",
            forecast=0.3, actual=0.5,
        )
    ]
    result = analyze_sentiment(nodes, events)
    assert isinstance(result, SentimentIndex)
    assert result.score > 0
    assert "Hawkish" in result.label


def test_sentiment_neutral_no_events():
    nodes: list[BootstrapNode] = []
    events: list[EconomicEvent] = []
    result = analyze_sentiment(nodes, events)
    assert result.score == 0.0
    assert result.label == "Neutral"
