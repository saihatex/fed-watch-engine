from __future__ import annotations

from typing import Sequence

from fedwatch.bias_engine import MacroBias
from fedwatch.bootstrap import BootstrapNode
from fedwatch.news_loader import EconomicEvent


def render_terminal_summary(nodes: list[BootstrapNode], current_rate: float) -> str:
    lines: list[str] = [
        "=================================================================",
        " BLOCK 1: FED WATCH ENGINE - FOMC RATE PATH",
        f" Current target midpoint: {current_rate:.3f}%",
        "-----------------------------------------------------------------",
        f" {'Decision Date':<15} {'Futures':<10} {'Implied Rate':<14} {'Market Pricing'}",
        "-----------------------------------------------------------------",
    ]

    for node in nodes:
        if node.meeting is None:
            continue

        dec_date = str(node.meeting.decision_date)
        price_str = f"{node.futures_price:.3f}" if node.futures_price else "N/A"
        rate_str = f"{node.rate_after:.3f}%"
        outcomes_str = str(node.outcomes) if node.outcomes else "N/A"

        sep_flag = " [SEP/Dots]" if node.meeting.has_sep else ""
        lines.append(f" {dec_date:<15} {price_str:<10} {rate_str:<14} {outcomes_str}{sep_flag}")

    lines.append("-----------------------------------------------------------------")
    return "\n".join(lines)


def render_macro_news_block(
    events: Sequence[EconomicEvent],
    window_title: str = "Today",
    source_label: str = "Live API (ForexFactory/MacroFeed)",
) -> str:
    lines: list[str] = [
        "",
        "=================================================================",
        f" BLOCK 2: ECONOMIC CALENDAR ({window_title.upper()}) - USD & EUR",
        f" Source: {source_label}",
        "-----------------------------------------------------------------",
        f" {'Impact':<8} {'Ccy':<5} {'Date & Time':<17} {'Event Name':<26} {'Act vs Fc (Status)'}",
        "-----------------------------------------------------------------",
    ]

    if not events:
        lines.append(f" No high/medium impact events scheduled for {window_title.lower()}.")
    else:
        for ev in events:
            date_time_str = f"{ev.event_date.strftime('%m-%d')} {ev.event_time}"
            act_str = f"{ev.actual}{ev.unit}" if ev.actual is not None else "TBA"
            fc_str = f"{ev.forecast}{ev.unit}" if ev.forecast is not None else "N/A"
            dev_str = f" ({ev.deviation:+.2f})" if ev.deviation is not None else ""
            comp_str = f"{act_str} vs {fc_str}{dev_str} [{ev.status}]"
            lines.append(f" [{ev.impact[0]}]      {ev.currency:<5} {date_time_str:<17} {ev.event_name:<26} {comp_str}")

    lines.append("-----------------------------------------------------------------")
    return "\n".join(lines)


def render_script_thoughts_block(bias: MacroBias) -> str:
    lines: list[str] = [
        "",
        "=================================================================",
        " BLOCK 3: SCRIPT'S MATH THOUGHTS & SMC TACTICAL PLAYBOOK",
        "-----------------------------------------------------------------",
        f" OVERALL MACRO BIAS:  {bias.overall_bias}",
        f" SENTIMENT SUMMARY:   {bias.sentiment_summary}",
    ]

    if bias.divergence_warning:
        lines.append("")
        lines.append(f" [WARNING] {bias.divergence_warning}")

    lines.append("")
    lines.append(" SMC TACTICAL PLAYBOOK:")
    for note in bias.smc_playbook:
        lines.append(f"   * {note}")

    lines.append("=================================================================")
    return "\n".join(lines)
