from __future__ import annotations

from datetime import date
from pathlib import Path

from fedwatch.bootstrap import BootstrapNode
from fedwatch.db import DEFAULT_DB, init_db, load_yesterday, save_snapshot


def persist_bootstrap_nodes(
    nodes: list[BootstrapNode],
    snapshot_date: date | None = None,
    db_path: Path = DEFAULT_DB,
) -> None:
    init_db(db_path)
    today = snapshot_date or date.today()

    for node in nodes:
        if node.meeting is not None and node.outcomes is not None:
            save_snapshot(
                snapshot_date=today,
                decision_date=node.meeting.decision_date,
                futures_price=node.futures_price,
                implied_rate=node.rate_after,
                probs=node.outcomes.probs,
                db_path=db_path,
            )


def format_delta_report(
    today_nodes: list[BootstrapNode],
    snapshot_date: date | None = None,
    db_path: Path = DEFAULT_DB,
) -> list[str]:
    today = snapshot_date or date.today()
    lines: list[str] = []

    for node in today_nodes:
        if node.meeting is None or node.outcomes is None:
            continue

        dec_date = node.meeting.decision_date
        prev = load_yesterday(today, dec_date, db_path)

        dominant_bp, dominant_prob = node.outcomes.dominant
        label = "hold" if dominant_bp == 0 else f"{dominant_bp:+d}bp"

        if prev is None:
            lines.append(f"FOMC {dec_date}: {label} ({dominant_prob*100:.0f}%) [no prior snapshot]")
        else:
            prev_prob = prev.get("prob_hold", 0.0) if dominant_bp == 0 else prev.get(f"prob_{'cut' if dominant_bp < 0 else 'hike'}{abs(dominant_bp)}", 0.0)
            diff = (dominant_prob - prev_prob) * 100
            sign = "+" if diff >= 0 else ""
            lines.append(f"FOMC {dec_date}: {label} {dominant_prob*100:.0f}% ({sign}{diff:.1f}% vs {prev['snapshot_date']})")

    return lines
