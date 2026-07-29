from __future__ import annotations

from fedwatch.bootstrap import BootstrapNode


def render_terminal_summary(nodes: list[BootstrapNode], current_rate: float) -> str:
    lines: list[str] = [
        "FED WATCH ENGINE - FOMC RATE PATH",
        f"Current target midpoint: {current_rate:.3f}%",
        "-" * 65,
        f"{'Decision Date':<15} {'Futures':<10} {'Implied Rate':<14} {'Market Pricing'}",
        "-" * 65,
    ]

    for node in nodes:
        if node.meeting is None:
            continue

        dec_date = str(node.meeting.decision_date)
        price_str = f"{node.futures_price:.3f}" if node.futures_price else "N/A"
        rate_str = f"{node.rate_after:.3f}%"
        outcomes_str = str(node.outcomes) if node.outcomes else "N/A"

        sep_flag = " [SEP/Dots]" if node.meeting.has_sep else ""
        lines.append(f"{dec_date:<15} {price_str:<10} {rate_str:<14} {outcomes_str}{sep_flag}")

    lines.append("-" * 65)
    return "\n".join(lines)
