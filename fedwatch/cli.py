from __future__ import annotations

from typing import Sequence

from rich import box
from rich.console import Group
from rich.panel import Panel
from rich.table import Table

from fedwatch.bias_engine import SentimentIndex, compute_market_divergence
from fedwatch.bootstrap import BootstrapNode
from fedwatch.news_loader import EconomicEvent


def render_fomc_path_block(nodes: list[BootstrapNode], current_rate: float) -> Panel:
    table = Table(show_header=True, box=box.SIMPLE)
    table.add_column("Date", width=12)
    table.add_column("ZQ", justify="right", width=10)
    table.add_column("Implied", justify="right", width=10)
    table.add_column("Pricing")

    for node in nodes:
        if node.meeting is None:
            continue
        sep = " (SEP)" if node.meeting.has_sep else ""
        outcomes_str = str(node.outcomes) if node.outcomes else "n/a"
        table.add_row(
            str(node.meeting.decision_date),
            f"{node.futures_price:.3f}",
            f"{node.rate_after:.3f}%",
            f"{outcomes_str}{sep}",
        )

    return Panel(
        table,
        title=f"FOMC rate path  |  target {current_rate:.3f}%",
        border_style="white",
    )


def render_event_table(events: Sequence[EconomicEvent], window_title: str, source_label: str) -> Panel:
    table = Table(show_header=True, box=box.SIMPLE)
    table.add_column("#", justify="center", width=3)
    table.add_column("Imp", width=4)
    table.add_column("Ccy", width=4)
    table.add_column("When", width=13)
    table.add_column("Event")
    table.add_column("Prev", justify="right", width=8)
    table.add_column("Fcst", justify="right", width=8)
    table.add_column("Actual", width=16)

    if not events:
        table.add_row("-", "-", "-", "-", f"No events ({window_title.lower()})", "-", "-", "-")
    else:
        for i, ev in enumerate(events, start=1):
            dt_str = f"{ev.event_date.strftime('%m-%d')} {ev.event_time}"
            prev_str = f"{ev.previous}{ev.unit}" if ev.previous is not None else "-"
            fc_str = f"{ev.forecast}{ev.unit}" if ev.forecast is not None else "-"
            if ev.actual is not None:
                act_str = f"{ev.actual}{ev.unit} ({ev.status})"
            else:
                act_str = f"- ({ev.status})"

            table.add_row(
                str(i),
                ev.impact[0].upper(),
                ev.currency,
                dt_str,
                ev.event_name,
                prev_str,
                fc_str,
                act_str,
            )

    return Panel(
        table,
        title=f"Calendar — {window_title}",
        subtitle=f"{source_label}  |  1-{len(events)} detail  |  G chart  |  B back",
        border_style="white",
    )


def render_sentiment_block(sentiment: SentimentIndex, delta_lines: list[str]) -> Panel:
    elements = []

    score_text = (
        f"Score: {sentiment.score:+.1f} ({sentiment.label})\n"
        f"Hawkish: {sentiment.hawkish_points:.1f}  Dovish: {sentiment.dovish_points:.1f}"
    )
    elements.append(Panel(score_text, title="Sentiment", border_style="white"))

    if sentiment.news_surprises:
        surp_lines = [f"  {name}: {dev:+.4f}" for name, dev in sentiment.news_surprises]
        elements.append(Panel("\n".join(surp_lines), title="Surprises", border_style="white"))

    if delta_lines:
        delta_text = "\n".join(f"  {line}" for line in delta_lines)
    else:
        delta_text = "  No prior snapshot"

    elements.append(Panel(delta_text, title="Delta vs prior snapshot", border_style="white"))

    return Panel(Group(*elements), title="Sentiment & delta", border_style="white")


def render_event_deep_dive(
    event_idx: int,
    event: EconomicEvent,
    nodes: Sequence[BootstrapNode],
    db_history: list[dict],
) -> Panel:
    is_rate_event = "Rate" in event.event_name or "FOMC" in event.event_name or "Federal Funds" in event.event_name
    div = compute_market_divergence(event, nodes)
    elements = []

    val_table = Table(show_header=True, box=box.SIMPLE)
    val_table.add_column("Previous", justify="center")
    val_table.add_column("Forecast", justify="center")
    val_table.add_column("Actual", justify="center")
    val_table.add_column("Status", justify="center")

    prev_str = f"{event.previous}{event.unit}" if event.previous is not None else "-"
    fc_str = f"{event.forecast}{event.unit}" if event.forecast is not None else "-"
    act_str = f"{event.actual}{event.unit}" if event.actual is not None else "-"

    val_table.add_row(prev_str, fc_str, act_str, event.status)
    elements.append(Panel(val_table, title="Values", border_style="white"))

    if is_rate_event:
        rate_lines = []
        if div["implied_rate"] is not None:
            rate_lines.append(f"Target midpoint: {div['rate_before']:.3f}%")
            rate_lines.append(f"Implied rate:    {div['implied_rate']:.3f}%")
            if div["market_divergence_bp"] is not None:
                rate_lines.append(f"Change:          {div['market_divergence_bp']:+.2f} bp")
        elements.append(Panel("\n".join(rate_lines) or "No rate data", title="Rate", border_style="white"))
    else:
        surp_lines = []
        if event.deviation is not None:
            surp_lines.append(f"Surprise: {event.deviation:+.4f} {event.unit}")
        else:
            surp_lines.append("Surprise: pending")
            if event.forecast is not None and event.previous is not None:
                diff = round(event.forecast - event.previous, 2)
                surp_lines.append(f"Forecast vs prev: {diff:+.2f} {event.unit}")
        elements.append(Panel("\n".join(surp_lines), title="Surprise", border_style="white"))

    hist_table = Table(show_header=True, box=box.SIMPLE)
    hist_table.add_column("Date", width=12)
    hist_table.add_column("Actual", justify="right", width=10)
    hist_table.add_column("Forecast", justify="right", width=10)
    hist_table.add_column("Previous", justify="right", width=10)
    hist_table.add_column("Dev", justify="right")

    matching_rows = sorted(
        [r for r in db_history if r.get("event_name") == event.event_name],
        key=lambda x: x["event_date"],
    )

    for row in reversed(matching_rows[-6:]):
        act_h = f"{row['actual']}{row.get('unit', '')}" if row.get("actual") is not None else "-"
        fc_h = f"{row['forecast']}{row.get('unit', '')}" if row.get("forecast") is not None else "-"
        prev_h = f"{row['previous']}{row.get('unit', '')}" if row.get("previous") is not None else "-"
        dev = row.get("deviation")
        dev_h = f"{dev:+.4f}" if dev is not None else "-"
        hist_table.add_row(str(row["event_date"]), act_h, fc_h, prev_h, dev_h)

    if not matching_rows:
        elements.append(Panel("No history", title="History", border_style="white"))
    else:
        elements.append(Panel(hist_table, title="History (last 6)", border_style="white"))

    return Panel(
        Group(*elements),
        title=f"#{event_idx}  {event.currency} {event.event_name}",
        subtitle=f"{event.event_date} {event.event_time}  |  {event.impact}  |  G chart  |  B back",
        border_style="white",
    )
