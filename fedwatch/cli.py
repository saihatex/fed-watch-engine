from __future__ import annotations

from datetime import date
from typing import Sequence

from fedwatch.bias_engine import SentimentIndex, compute_market_divergence
from fedwatch.bootstrap import BootstrapNode
from fedwatch.news_loader import EconomicEvent


def render_fomc_path_block(nodes: list[BootstrapNode], current_rate: float) -> str:
    lines: list[str] = [
        "==================================================================",
        " FED WATCH  |  FOMC RATE PATH (ZQ Futures)",
        f" Current target midpoint: {current_rate:.3f}%",
        "-----------------------------------------------------------------",
        f" {'Decision Date':<15} {'Futures':<10} {'Implied Rate':<14} {'Market Pricing'}",
        "-----------------------------------------------------------------",
    ]
    for node in nodes:
        if node.meeting is None:
            continue
        dec_date = str(node.meeting.decision_date)
        price_str = f"{node.futures_price:.3f}"
        rate_str = f"{node.rate_after:.3f}%"
        outcomes_str = str(node.outcomes) if node.outcomes else "N/A"
        sep_flag = "  [SEP]" if node.meeting.has_sep else ""
        lines.append(f" {dec_date:<15} {price_str:<10} {rate_str:<14} {outcomes_str}{sep_flag}")
    lines.append("-----------------------------------------------------------------")
    return "\n".join(lines)


def render_event_table(events: Sequence[EconomicEvent], window_title: str, source_label: str) -> str:
    lines: list[str] = [
        "",
        "=================================================================",
        f" BLOCK 2  |  ECONOMIC CALENDAR ({window_title.upper()}) -- USD & EUR",
        f" Source : {source_label}",
        "-----------------------------------------------------------------",
        f" {'#':<4} {'!':<4} {'CCY':<5} {'DATE  TIME':<14} {'EVENT NAME':<30} {'ACT vs FC'}",
        "-----------------------------------------------------------------",
    ]
    if not events:
        lines.append(f" No high/medium impact events for {window_title.lower()}.")
    else:
        for i, ev in enumerate(events, start=1):
            dt_str = f"{ev.event_date.strftime('%m-%d')} {ev.event_time}"
            act_str = f"{ev.actual}{ev.unit}" if ev.actual is not None else "TBA"
            fc_str = f"{ev.forecast}{ev.unit}" if ev.forecast is not None else "N/A"
            dev_str = f" ({ev.deviation:+.2f})" if ev.deviation is not None else ""
            comp_str = f"{act_str} vs {fc_str}{dev_str} [{ev.status}]"
            lines.append(f" {i:<4} [{ev.impact[0]}]  {ev.currency:<5} {dt_str:<14} {ev.event_name:<30} {comp_str}")
    lines.append("-----------------------------------------------------------------")
    lines.append(" Enter # for deep dive   |   G = Fed Path chart   |   B = Back")
    lines.append("=================================================================")
    return "\n".join(lines)


def render_sentiment_block(sentiment: SentimentIndex, delta_lines: list[str]) -> str:
    lines: list[str] = [
        "",
        "=================================================================",
        " BLOCK 3  |  SENTIMENT INDEX & DELTA REPORT",
        "-----------------------------------------------------------------",
        f" {sentiment}",
        f" Hawkish pts: {sentiment.hawkish_points:.1f}  |  Dovish pts: {sentiment.dovish_points:.1f}",
    ]
    if sentiment.news_surprises:
        lines.append(" News surprises:")
        for name, dev in sentiment.news_surprises:
            sign = "+" if dev >= 0 else ""
            lines.append(f"   {name}: {sign}{dev:.4f}")
    lines.append("")
    lines.append(" Daily Delta vs Previous Snapshot:")
    if delta_lines:
        for line in delta_lines:
            lines.append(f"   {line}")
    else:
        lines.append("   No prior snapshot available.")
    lines.append("=================================================================")
    return "\n".join(lines)


def render_event_deep_dive(
    event_idx: int,
    event: EconomicEvent,
    nodes: Sequence[BootstrapNode],
    db_history: list[dict],
) -> str:
    div = compute_market_divergence(event, nodes)
    lines: list[str] = [
        "",
        "=================================================================",
        f" DEEP DIVE  |  #{event_idx} {event.currency}  {event.event_name}",
        f" Date/Time : {event.event_date}  {event.event_time}  |  Impact: {event.impact}",
        "-----------------------------------------------------------------",
        " MARKET DIVERGENCE",
    ]

    if div["forecast"] is not None:
        fc_str = f"{div['forecast']}{div['unit']}"
        act_str = f"{div['actual']}{div['unit']}" if div["actual"] is not None else "TBA"
        dev_str = f"{div['deviation']:+.4f}" if div["deviation"] is not None else "N/A"
        lines.append(f"   Forecast  : {fc_str}")
        lines.append(f"   Actual    : {act_str}")
        lines.append(f"   Deviation : {dev_str} {div['unit']}")
    else:
        lines.append("   No forecast data.")

    if div["implied_rate"] is not None:
        lines.append(f"   Fed implied rate (next FOMC) : {div['implied_rate']:.3f}%")
        lines.append(f"   Rate before meeting           : {div['rate_before']:.3f}%")
    if div["market_divergence_bp"] is not None:
        lines.append(f"   Market divergence in bp       : {div['market_divergence_bp']:+.2f} bp")

    lines.append("")
    lines.append(" HISTORICAL RELEASES (last 3 from DB)")
    lines.append(f"   {'Date':<12} {'Actual':<12} {'Forecast':<12} {'Previous':<12} {'Deviation'}")
    lines.append("   " + "-" * 56)

    shown = 0
    for row in reversed(db_history):
        if row.get("event_name") == event.event_name:
            act_h = f"{row['actual']}{row.get('unit','')}" if row.get("actual") is not None else "N/A"
            fc_h = f"{row['forecast']}{row.get('unit','')}" if row.get("forecast") is not None else "N/A"
            prev_h = f"{row['previous']}{row.get('unit','')}" if row.get("previous") is not None else "N/A"
            dev_h = f"{row['deviation']:+.4f}" if row.get("deviation") is not None else "N/A"
            lines.append(f"   {row['event_date']:<12} {act_h:<12} {fc_h:<12} {prev_h:<12} {dev_h}")
            shown += 1
            if shown >= 3:
                break

    if shown == 0:
        lines.append("   No historical data yet in database.")

    lines.append("-----------------------------------------------------------------")
    lines.append(" B = Back to event list")
    lines.append("=================================================================")
    return "\n".join(lines)
