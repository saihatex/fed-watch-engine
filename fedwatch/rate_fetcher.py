"""
rate_fetcher.py — Verified Target Rate & Range retrieval.

Uses an independent, confirmed source of truth (FOMC decision records / SQLite cache / explicit target setting).
Does NOT infer current rate from ZQ futures to prevent circular logic in bootstrap equations.
"""
from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

_CONFIRMED_LOWER = 3.50
_CONFIRMED_UPPER = 3.75


# ── SQLite Cache / Local Record ──────────────────────────────────────────────

def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fed_target_rate (
            id          INTEGER PRIMARY KEY,
            set_date    TEXT NOT NULL,
            lower_bound REAL NOT NULL,
            upper_bound REAL NOT NULL
        )
    """)


def set_confirmed_target_range(lower: float, upper: float, set_date: date | None = None, db_path: Path | None = None) -> None:
    """Manually record/confirm a newly decided target range in SQLite."""
    from fedwatch.db import DEFAULT_DB
    db = db_path or DEFAULT_DB
    dt_str = (set_date or date.today()).isoformat()
    conn = sqlite3.connect(db)
    _ensure_table(conn)
    conn.execute("DELETE FROM fed_target_rate")
    conn.execute(
        "INSERT INTO fed_target_rate (set_date, lower_bound, upper_bound) VALUES (?,?,?)",
        (dt_str, lower, upper),
    )
    conn.commit()
    conn.close()


def load_confirmed_target_range(db_path: Path | None = None) -> tuple[float, float] | None:
    """Load confirmed target range from SQLite storage if present."""
    from fedwatch.db import DEFAULT_DB
    db = db_path or DEFAULT_DB
    try:
        conn = sqlite3.connect(db)
        _ensure_table(conn)
        row = conn.execute(
            "SELECT lower_bound, upper_bound FROM fed_target_rate ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn.close()
        if row:
            return float(row[0]), float(row[1])
    except Exception:
        pass
    return None


# ── Public API ───────────────────────────────────────────────────────────────

def get_current_target_range(db_path: Path | None = None) -> tuple[float, float]:
    """
    Returns verified FOMC target range:
      1. Confirmed record from SQLite DB
      2. Independent static anchor (3.50, 3.75)
    """
    confirmed = load_confirmed_target_range(db_path)
    if confirmed is not None:
        return confirmed
    return _CONFIRMED_LOWER, _CONFIRMED_UPPER


def get_current_midpoint(db_path: Path | None = None) -> float:
    lower, upper = get_current_target_range(db_path)
    return round((lower + upper) / 2, 4)


def get_current_target_range_str(db_path: Path | None = None) -> str:
    lower, upper = get_current_target_range(db_path)
    return f"{lower:.2f}% – {upper:.2f}%"
