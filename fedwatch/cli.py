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
    table = Table(expand=True, show_header=True, header_style="bold cyan", box=box.ROUNDED)
    table.add_column("Decision Date", style="bold white", width=15)
    table.add_column("Futures", style="bright_blue", justify="right", width=10)
    table.add_column("Implied Rate", style="bold yellow", justify="right", width=14)
    table.add_column("Market Pricing", style="bold white")

    for node in nodes:
        if node.meeting is None:
            continue
        dec_date = str(node.meeting.decision_date)
        price_str = f"{node.futures_price:.3f}"
        rate_str = f"{node.rate_after:.3f}%"
        outcomes_str = str(node.outcomes) if node.outcomes else "N/A"
        sep_badge = "  [bold magenta]SEP[/bold magenta]" if node.meeting.has_sep else ""
        table.add_row(dec_date, price_str, rate_str, f"{outcomes_str}{sep_badge}")

    return Panel(
        table,
        title="[bold cyan]FED WATCH | FOMC RATE PATH (ZQ Futures)[/bold cyan]",
        subtitle=f"Current target midpoint: [bold yellow]{current_rate:.3f}%[/bold yellow]",
        subtitle_align="left",
        border_style="cyan",
        box=box.ROUNDED,
    )


def render_event_table(events: Sequence[EconomicEvent], window_title: str, source_label: str) -> Panel:
    table = Table(expand=True, show_header=True, header_style="bold cyan", box=box.ROUNDED)
    table.add_column("#", justify="center", style="bold cyan", width=3)
    table.add_column("!", justify="center", width=3)
    table.add_column("CCY", justify="center", style="bold white", width=5)
    table.add_column("Date / Time", style="cyan", width=13)
    table.add_column("Event Name", style="bold white")
    table.add_column("Current", justify="right", style="dim", width=9)
    table.add_column("Forecast", justify="right", style="yellow", width=9)
    table.add_column("Actual (Status)", justify="left")

    if not events:
        table.add_row("-", "-", "-", "-", f"No high/medium impact events for {window_title.lower()}.", "-", "-", "-")
    else:
        for i, ev in enumerate(events, start=1):
            dt_str = f"{ev.event_date.strftime('%m-%d')} {ev.event_time}"
            cur_str = f"{ev.previous}{ev.unit}" if ev.previous is not None else "N/A"
            fc_str = f"{ev.forecast}{ev.unit}" if ev.forecast is not None else "N/A"

            imp_code = ev.impact[0].upper()
            if imp_code == "H":
                imp_str = "[bold red]H[/bold red]"
            elif imp_code == "M":
                imp_str = "[bold yellow]M[/bold yellow]"
            else:
                imp_str = "[dim]L[/dim]"

            if ev.actual is not None:
                if ev.deviation is not None and ev.deviation > 0:
                    act_str = f"[bold green]{ev.actual}{ev.unit}[/bold green]"
                elif ev.deviation is not None and ev.deviation < 0:
                    act_str = f"[bold red]{ev.actual}{ev.unit}[/bold red]"
                else:
                    act_str = f"[bold white]{ev.actual}{ev.unit}[/bold white]"
                status_str = f"[green]{ev.status}[/green]"
            else:
                act_str = "[dim]TBA[/dim]"
                status_str = f"[dim]{ev.status}[/dim]"

            table.add_row(
                str(i),
                imp_str,
                f"[bold cyan]{ev.currency}[/bold cyan]",
                dt_str,
                ev.event_name,
                cur_str,
                fc_str,
                f"{act_str} ({status_str})",
            )

    if "ForexFactory" in source_label:
        src_fmt = f"{source_label}  [bold green]LIVE[/bold green]"
    else:
        src_fmt = f"{source_label}"

    return Panel(
        table,
        title=f"[bold cyan]ECONOMIC CALENDAR ({window_title.upper()}) -- USD & EUR[/bold cyan]",
        subtitle=f"Source: {src_fmt} | [bold yellow]1-{len(events)}[/bold yellow] Deep Dive | [bold yellow]G[/bold yellow] Fed Path | [bold yellow]B[/bold yellow] Back",
        subtitle_align="left",
        border_style="blue",
        box=box.ROUNDED,
    )


def render_sentiment_block(sentiment: SentimentIndex, delta_lines: list[str]) -> Panel:
    elements = []

    score_val = sentiment.score
    if score_val > 0:
        score_label = f"[bold red]HAWKISH (+{score_val:.1f})[/bold red]"
    elif score_val < 0:
        score_label = f"[bold green]DOVISH ({score_val:.1f})[/bold green]"
    else:
        score_label = "[bold white]NEUTRAL (0.0)[/bold white]"

    bar_pos = int((score_val + 100) / 200 * 30)
    bar_pos = max(0, min(30, bar_pos))
    bar_str = "[green]" + "=" * bar_pos + "[/green]" + "[white]|[/white]" + "[red]" + "=" * (30 - bar_pos) + "[/red]"

    sentiment_text = (
        f"Stance: {score_label}\n"
        f"Scale : [green]DOVISH[/green] {bar_str} [red]HAWKISH[/red]\n"
        f"Points: Hawkish [red]{sentiment.hawkish_points:.1f}[/red]  |  Dovish [green]{sentiment.dovish_points:.1f}[/green]"
    )
    elements.append(Panel(sentiment_text, title="[bold]Market Sentiment Index[/bold]", border_style="yellow", box=box.ROUNDED))

    if sentiment.news_surprises:
        surp_lines = []
        for name, dev in sentiment.news_surprises:
            if dev >= 0:
                surp_lines.append(f"  > {name}: [bold green]+{dev:.4f}[/bold green]")
            else:
                surp_lines.append(f"  > {name}: [bold red]{dev:.4f}[/bold red]")
        surp_text = "\n".join(surp_lines)
        elements.append(Panel(surp_text, title="[bold]News Release Surprises[/bold]", border_style="cyan", box=box.ROUNDED))

    if delta_lines:
        delta_text = "\n".join([f"  > {l}" for l in delta_lines])
    else:
        delta_text = "  [dim]No prior snapshot available.[/dim]"

    elements.append(Panel(delta_text, title="[bold]Daily Delta vs Previous Snapshot[/bold]", border_style="blue", box=box.ROUNDED))

    return Panel(
        Group(*elements),
        title="[bold cyan]SENTIMENT INDEX & DELTA REPORT[/bold cyan]",
        border_style="magenta",
        box=box.ROUNDED,
    )


def render_event_deep_dive(
    event_idx: int,
    event: EconomicEvent,
    nodes: Sequence[BootstrapNode],
    db_history: list[dict],
) -> Panel:
    is_rate_event = "Rate" in event.event_name or "FOMC" in event.event_name or "Federal Funds" in event.event_name
    div = compute_market_divergence(event, nodes)

    elements = []

    val_table = Table(show_header=True, header_style="bold cyan", expand=True, box=box.ROUNDED)
    val_table.add_column("Previous", style="dim", justify="center")
    val_table.add_column("Forecast", style="yellow", justify="center")
    val_table.add_column("Actual", style="bold white", justify="center")
    val_table.add_column("Status", justify="center")

    prev_str = f"{event.previous}{event.unit}" if event.previous is not None else "N/A"
    fc_str = f"{event.forecast}{event.unit}" if event.forecast is not None else "N/A"
    if event.actual is not None:
        if event.deviation is not None and event.deviation > 0:
            act_str = f"[bold green]{event.actual}{event.unit}[/bold green]"
        elif event.deviation is not None and event.deviation < 0:
            act_str = f"[bold red]{event.actual}{event.unit}[/bold red]"
        else:
            act_str = f"[bold white]{event.actual}{event.unit}[/bold white]"
        st_str = f"[green]{event.status}[/green]"
    else:
        act_str = "[dim]TBA[/dim]"
        st_str = f"[dim]{event.status}[/dim]"

    val_table.add_row(prev_str, fc_str, act_str, st_str)
    elements.append(Panel(val_table, title="[bold]Value Breakdown[/bold]", border_style="blue", box=box.ROUNDED))

    if is_rate_event:
        rate_lines = []
        if div["implied_rate"] is not None:
            rate_lines.append(f"Target Rate / Midpoint : [bold yellow]{div['rate_before']:.3f}%[/bold yellow]")
            rate_lines.append(f"Futures Implied Rate   : [bold cyan]{div['implied_rate']:.3f}%[/bold cyan]")
            if div["market_divergence_bp"] is not None:
                rate_lines.append(f"Implied Rate Change    : [bold white]{div['market_divergence_bp']:+.2f} bp[/bold white]")
        rate_lines.append("\n[dim]Press G to open interactive Fed Path Rate Curve chart.[/dim]")
        elements.append(Panel("\n".join(rate_lines), title="[bold]Central Bank Rate Analysis & Divergence[/bold]", border_style="cyan", box=box.ROUNDED))
    else:
        surp_lines = []
        if event.deviation is not None:
            dev_val = event.deviation
            if dev_val > 0:
                dev_str = f"[bold green]+{dev_val:.4f} {event.unit}[/bold green]"
            elif dev_val < 0:
                dev_str = f"[bold red]{dev_val:.4f} {event.unit}[/bold red]"
            else:
                dev_str = f"[bold white]0.0000 {event.unit}[/bold white]"
            surp_lines.append(f"Latest Surprise (Dev): {dev_str}")
        else:
            surp_lines.append("Surprise (Dev): [dim]Pending release (Actual is TBA)[/dim]")
            if event.forecast is not None and event.previous is not None:
                diff = round(event.forecast - event.previous, 2)
                surp_lines.append(f"Forecast vs Current: [yellow]{diff:+.2f} {event.unit}[/yellow] expected change")

        surp_lines.append("\n[dim]Press G to open Historical Actual vs Forecast Bar Chart.[/dim]")
        elements.append(Panel("\n".join(surp_lines), title="[bold]Surprise Analysis[/bold]", border_style="cyan", box=box.ROUNDED))

    hist_table = Table(show_header=True, header_style="bold cyan", expand=True, box=box.ROUNDED)
    hist_table.add_column("Date", style="cyan", width=12)
    hist_table.add_column("Actual", justify="right", width=10)
    hist_table.add_column("Forecast", justify="right", style="yellow", width=10)
    hist_table.add_column("Previous", justify="right", style="dim", width=10)
    hist_table.add_column("Deviation", justify="right")

    matching_rows = [r for r in db_history if r.get("event_name") == event.event_name]
    matching_rows = sorted(matching_rows, key=lambda x: x["event_date"])
    shown = 0

    for row in reversed(matching_rows):
        act_h = f"{row['actual']}{row.get('unit','')}" if row.get("actual") is not None else "N/A"
        fc_h = f"{row['forecast']}{row.get('unit','')}" if row.get("forecast") is not None else "N/A"
        prev_h = f"{row['previous']}{row.get('unit','')}" if row.get("previous") is not None else "N/A"

        dev = row.get("deviation")
        if dev is not None:
            if dev > 0:
                dev_h = f"[bold green]+{dev:.4f}[/bold green]"
            elif dev < 0:
                dev_h = f"[bold red]{dev:.4f}[/bold red]"
            else:
                dev_h = "[white]0.0000[/white]"
        else:
            dev_h = "[dim]N/A[/dim]"

        hist_table.add_row(str(row["event_date"]), act_h, fc_h, prev_h, dev_h)
        shown += 1
        if shown >= 6:
            break

    if shown == 0:
        hist_panel = Panel("[dim]No historical releases logged yet.[/dim]", title="[bold]Historical Releases (Last 6 Database Releases)[/bold]", border_style="magenta", box=box.ROUNDED)
    else:
        hist_panel = Panel(hist_table, title="[bold]Historical Releases (Last 6 Database Releases)[/bold]", border_style="magenta", box=box.ROUNDED)

    elements.append(hist_panel)

    imp_color = "red" if event.impact.lower() == "high" else ("yellow" if event.impact.lower() == "medium" else "dim")

    return Panel(
        Group(*elements),
        title=f"[bold cyan]DEEP DIVE #{event_idx}[/bold cyan] | [bold white]{event.currency} {event.event_name}[/bold white]",
        subtitle=f"Date/Time: {event.event_date} {event.event_time} | Impact: [{imp_color}]{event.impact}[/{imp_color}] | [bold yellow]G[/bold yellow] Chart | [bold yellow]B[/bold yellow] Back",
        subtitle_align="left",
        border_style="green",
        box=box.ROUNDED,
    )
