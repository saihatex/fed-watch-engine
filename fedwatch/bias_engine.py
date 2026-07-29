from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from fedwatch.bootstrap import BootstrapNode
from fedwatch.news_loader import EconomicEvent


@dataclass
class SentimentIndex:
    score: float
    label: str
    hawkish_points: float
    dovish_points: float
    news_surprises: list[tuple[str, float]]

    def __str__(self) -> str:
        bar_pos = int((self.score + 100) / 200 * 30)
        bar = "-" * bar_pos + "|" + "-" * (30 - bar_pos)
        return f"[DOVISH {bar} HAWKISH]  Score: {self.score:+.1f}  ({self.label})"


def _rate_path_contribution(nodes: Sequence[BootstrapNode]) -> tuple[float, float]:
    hike = 0.0
    cut = 0.0
    for node in nodes:
        if node.outcomes:
            hike += node.outcomes.probs.get(25, 0.0) + node.outcomes.probs.get(50, 0.0) * 1.5
            cut += node.outcomes.probs.get(-25, 0.0) + node.outcomes.probs.get(-50, 0.0) * 1.5
    return hike, cut


def analyze_sentiment(
    nodes: Sequence[BootstrapNode],
    events: Sequence[EconomicEvent],
) -> SentimentIndex:
    fed_hike, fed_cut = _rate_path_contribution(nodes)

    hawkish_pts = 0.0
    dovish_pts = 0.0
    surprises: list[tuple[str, float]] = []

    if fed_hike > fed_cut:
        hawkish_pts += min(fed_hike * 30, 50.0)
    elif fed_cut > fed_hike:
        dovish_pts += min(fed_cut * 30, 50.0)

    for ev in events:
        if ev.deviation is None:
            continue
        dev = ev.deviation
        name = ev.event_name

        if any(k in name for k in ("CPI", "PCE", "PPI", "Inflation")):
            contrib = dev * 20.0
        elif any(k in name for k in ("Payrolls", "NFP", "Employment", "Unemployment")):
            contrib = dev * 0.1
        elif any(k in name for k in ("GDP", "Retail")):
            contrib = dev * 15.0
        elif any(k in name for k in ("PMI", "ISM")):
            contrib = dev * 8.0
        elif "Rate" in name:
            contrib = dev * 25.0
        else:
            contrib = dev * 5.0

        if ev.impact == "Medium":
            contrib *= 0.6

        if contrib > 0:
            hawkish_pts += min(abs(contrib), 25.0)
        else:
            dovish_pts += min(abs(contrib), 25.0)

        surprises.append((name, round(dev, 4)))

    raw = hawkish_pts - dovish_pts
    score = max(-100.0, min(100.0, raw))

    if score > 60:
        label = "Strongly Hawkish"
    elif score > 25:
        label = "Hawkish"
    elif score > 5:
        label = "Mildly Hawkish"
    elif score < -60:
        label = "Strongly Dovish"
    elif score < -25:
        label = "Dovish"
    elif score < -5:
        label = "Mildly Dovish"
    else:
        label = "Neutral"

    return SentimentIndex(
        score=score,
        label=label,
        hawkish_points=hawkish_pts,
        dovish_points=dovish_pts,
        news_surprises=surprises,
    )


def compute_market_divergence(
    event: EconomicEvent,
    nodes: Sequence[BootstrapNode],
) -> dict:
    closest_node = None
    for node in nodes:
        if node.meeting is not None:
            closest_node = node
            break

    result = {
        "event_name": event.event_name,
        "forecast": event.forecast,
        "actual": event.actual,
        "deviation": event.deviation,
        "unit": event.unit,
        "implied_rate": None,
        "rate_before": None,
        "market_divergence_bp": None,
    }

    if closest_node is not None:
        result["implied_rate"] = closest_node.rate_after
        result["rate_before"] = closest_node.rate_before
        if event.deviation is not None and closest_node.rate_after is not None:
            result["market_divergence_bp"] = round(event.deviation * 100, 2)

    return result
