from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from fedwatch.bootstrap import BootstrapNode
from fedwatch.news_loader import EconomicEvent


@dataclass
class MacroBias:
    overall_bias: str
    hawkish_score: float
    dovish_score: float
    sentiment_summary: str
    divergence_warning: str | None
    smc_playbook: list[str]


def analyze_macro_bias(
    nodes: Sequence[BootstrapNode],
    events: Sequence[EconomicEvent],
) -> MacroBias:
    hawkish_points = 0.0
    dovish_points = 0.0

    # 1. Analyze Fed Funds Rate Path
    fed_hike_prob = 0.0
    fed_cut_prob = 0.0
    for node in nodes:
        if node.outcomes:
            fed_hike_prob += node.outcomes.probs.get(25, 0.0) + node.outcomes.probs.get(50, 0.0)
            fed_cut_prob += node.outcomes.probs.get(-25, 0.0) + node.outcomes.probs.get(-50, 0.0)

    if fed_hike_prob > fed_cut_prob:
        hawkish_points += 2.0
        fed_sentiment = f"Fed curve is pricing HAWKISH expectations ({fed_hike_prob*100:.0f}% total hike probability across upcoming meetings)."
    elif fed_cut_prob > fed_hike_prob:
        dovish_points += 2.0
        fed_sentiment = f"Fed curve is pricing DOVISH expectations ({fed_cut_prob*100:.0f}% total cut probability across upcoming meetings)."
    else:
        fed_sentiment = "Fed curve is pricing NEUTRAL/STABLE interest rate path."

    # 2. Analyze Macro Economic Events Deviation
    news_surprises: list[str] = []
    has_high_impact_usd = False

    for ev in events:
        if ev.impact == "High" and ev.currency == "USD":
            has_high_impact_usd = True

        if ev.deviation is not None:
            # Positive inflation/growth surprise => Hawkish (USD+)
            if "CPI" in ev.event_name or "PCE" in ev.event_name or "PPI" in ev.event_name:
                if ev.deviation > 0:
                    hawkish_points += 1.5
                    news_surprises.append(f"{ev.event_name} actual > forecast (+{ev.deviation:.2f}%) -> Inflation pressure")
                elif ev.deviation < 0:
                    dovish_points += 1.5
                    news_surprises.append(f"{ev.event_name} actual < forecast ({ev.deviation:.2f}%) -> Cooling inflation")

            # Labor Market Surprise (NFP/Payrolls)
            elif "Payrolls" in ev.event_name or "NFP" in ev.event_name:
                if ev.deviation > 0:
                    hawkish_points += 1.5
                    news_surprises.append(f"{ev.event_name} beat (+{ev.deviation:.0f}K) -> Tight labor market")
                elif ev.deviation < 0:
                    dovish_points += 1.5
                    news_surprises.append(f"{ev.event_name} miss ({ev.deviation:.0f}K) -> Weakening employment")

    # 3. Detect Divergence
    divergence_warning = None
    if hawkish_points > dovish_points and fed_cut_prob > 0.5:
        divergence_warning = "HAWKISH DIVERGENCE: Macro data is hot (inflation/jobs beat), but Fed curve is heavily pricing rate cuts. Expect repricing volatility!"
    elif dovish_points > hawkish_points and fed_hike_prob > 0.5:
        divergence_warning = "DOVISH DIVERGENCE: Macro data is cooling (cpi/jobs miss), but Fed curve is pricing rate hikes. Potential dovish pivot ahead."

    # 4. Generate SMC (Smart Money Concepts) Playbook
    smc_playbook: list[str] = []

    if has_high_impact_usd:
        smc_playbook.append("[SMC Alert] High-Impact USD release today: Expect liquidity sweep of Asian High / Asian Low before true directional expansion.")
        smc_playbook.append("[Execution] Avoid opening positions 15 mins prior to release; watch for 5m FVG (Fair Value Gap) displacement after initial spike.")
    else:
        smc_playbook.append("[SMC Alert] Standard volatility environment. Focus on London/NY session Order Blocks and liquidity pools.")

    if hawkish_points > dovish_points:
        overall_bias = "HAWKISH (USD BULLISH)"
        smc_playbook.append("[Scenario] Bullish USD / Bearish EURUSD: Look for premium array rejections and bearish displacement.")
    elif dovish_points > hawkish_points:
        overall_bias = "DOVISH (USD BEARISH)"
        smc_playbook.append("[Scenario] Bearish USD / Bullish EURUSD: Look for discount array rejections and bullish displacement.")
    else:
        overall_bias = "NEUTRAL"
        smc_playbook.append("[Scenario] Range-bound environment: Trade liquidity sweeps on both sides of the session range.")

    return MacroBias(
        overall_bias=overall_bias,
        hawkish_score=hawkish_points,
        dovish_score=dovish_points,
        sentiment_summary=fed_sentiment,
        divergence_warning=divergence_warning,
        smc_playbook=smc_playbook,
    )
