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
        f" ECONOMIC CALENDAR ({window_title.upper()}) -- USD & EUR",
        f" Source : {source_label}",
        "-----------------------------------------------------------------",
        f" {'#':<3} {'!':<3} {'CCY':<4} {'DATE  TIME':<13} {'EVENT NAME':<25} {'CURRENT':<9} {'FORECAST':<9} {'ACTUAL (STATUS)'}",
        "-----------------------------------------------------------------",
    ]
    if not events:
        lines.append(f" No high/medium impact events for {window_title.lower()}.")
    else:
        for i, ev in enumerate(events, start=1):
            dt_str = f"{ev.event_date.strftime('%m-%d')} {ev.event_time}"
            cur_str = f"{ev.previous}{ev.unit}" if ev.previous is not None else "N/A"
            fc_str = f"{ev.forecast}{ev.unit}" if ev.forecast is not None else "N/A"
            act_str = f"{ev.actual}{ev.unit}" if ev.actual is not None else "TBA"
            lines.append(
                f" {i:<3} [{ev.impact[0]}] {ev.currency:<4} {dt_str:<13} {ev.event_name:<25} {cur_str:<9} {fc_str:<9} {act_str} [{ev.status}]"
            )
    lines.append("-----------------------------------------------------------------")
    lines.append(" Enter # for deep dive   |   G = Fed Path chart   |   B = Back")
    lines.append("=================================================================")
    return "\n".join(lines)


def render_sentiment_block(sentiment: SentimentIndex, delta_lines: list[str]) -> str:
    lines: list[str] = [
        "",
        "=================================================================",
        " SENTIMENT INDEX & DELTA REPORT",
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
    is_rate_event = "Rate" in event.event_name or "FOMC" in event.event_name or "Federal Funds" in event.event_name
    div = compute_market_divergence(event, nodes)

    lines: list[str] = [
        "",
        "=================================================================",
        f" DEEP DIVE  |  #{event_idx} {event.currency}  {event.event_name}",
        f" Date/Time : {event.event_date}  {event.event_time}  |  Impact: {event.impact}",
        "-----------------------------------------------------------------",
        " VALUE BREAKDOWN",
        f"   Current (Prev) : {event.previous}{event.unit}" if event.previous is not None else "   Current (Prev) : N/A",
        f"   Forecast       : {event.forecast}{event.unit}" if event.forecast is not None else "   Forecast       : N/A",
        f"   Actual         : {event.actual}{event.unit}" if event.actual is not None else "   Actual         : TBA [To Be Announced]",
        "-----------------------------------------------------------------",
    ]

    if is_rate_event:
        lines.append(" CENTRAL BANK RATE ANALYSIS & DIVERGENCE")
        if div["implied_rate"] is not None:
            lines.append(f"   Target Rate / Midpoint  : {div['rate_before']:.3f}%")
            lines.append(f"   Futures Implied Rate    : {div['implied_rate']:.3f}%")
            if div["market_divergence_bp"] is not None:
                lines.append(f"   Implied Rate Change     : {div['market_divergence_bp']:+.2f} bp")
        lines.append("   Chart mode: Press G to open interactive Fed Path Rate Curve.")
    else:
        lines.append(" SURPRISE & EUR/USD IMPACT ANALYSIS")
        if event.deviation is not None:
            dev_val = event.deviation
            dev_str = f"{dev_val:+.4f} {event.unit}"
            lines.append(f"   Latest Surprise (Dev)   : {dev_str}")

            # Impact estimation logic
            if event.currency == "USD":
                pips = round(dev_val * (20 if "%" in event.unit else 0.1), 1)
                bias = "USD BULLISH / EURUSD BEARISH" if pips > 0 else "USD BEARISH / EURUSD BULLISH"
                lines.append(f"   Est. EURUSD Impact      : {bias} (~{abs(pips)} pips move)")
            else:
                pips = round(dev_val * (20 if "%" in event.unit else 0.1), 1)
                bias = "EUR BULLISH / EURUSD BULLISH" if pips > 0 else "EUR BEARISH / EURUSD BEARISH"
                lines.append(f"   Est. EURUSD Impact      : {bias} (~{abs(pips)} pips move)")
        else:
            lines.append("   Surprise (Dev)          : Pending release (Actual is TBA)")
            if event.forecast is not None and event.previous is not None:
                diff = round(event.forecast - event.previous, 2)
                lines.append(f"   Forecast vs Current     : {diff:+.2f} {event.unit} expected change")

        lines.append("   Chart mode: Press G to open Historical Actual vs Forecast Bar Chart.")

    lines.append("")
    lines.append(" HISTORICAL RELEASES (Last 6 from Database)")
    lines.append(f"   {'Date':<12} {'Actual':<10} {'Forecast':<10} {'Previous':<10} {'Deviation'}")
    lines.append("   " + "-" * 54)

    shown = 0
    matching_rows = [r for r in db_history if r.get("event_name") == event.event_name]
    matching_rows = sorted(matching_rows, key=lambda x: x["event_date"])

    for row in reversed(matching_rows):
        act_h = f"{row['actual']}{row.get('unit','')}" if row.get("actual") is not None else "N/A"
        fc_h = f"{row['forecast']}{row.get('unit','')}" if row.get("forecast") is not None else "N/A"
        prev_h = f"{row['previous']}{row.get('unit','')}" if row.get("previous") is not None else "N/A"
        dev_h = f"{row['deviation']:+.4f}" if row.get("deviation") is not None else "N/A"
        lines.append(f"   {row['event_date']:<12} {act_h:<10} {fc_h:<10} {prev_h:<10} {dev_h}")
        shown += 1
        if shown >= 6:
            break

    if shown == 0:
        lines.append("   No historical releases logged yet.")

    lines.append("-----------------------------------------------------------------")
    lines.append(" G = Open Chart (Line / Bar)   |   B = Back to Event List")
    lines.append("=================================================================")
    return "\n".join(lines)
