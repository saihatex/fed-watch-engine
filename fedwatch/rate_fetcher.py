"""
rate_fetcher.py — Live Target Rate & Range computation.

Primary source: Front-month ZQ Fed Funds Futures (CME via yfinance).
Implied rate = 100 - front_month_futures_price.
Target range = (round(implied_rate - 0.125, 2), round(implied_rate + 0.125, 2)).

Cache: SQLite table `fed_target_rate` in fedwatch.db.
Fallback chain: ZQ Front-Month → SQLite Cache → Hardcoded (3.50, 3.75).
"""
from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

from fedwatch.futures_loader import get_futures_price

_HARDCODED_LOWER = 3.50
_HARDCODED_UPPER = 3.75


def fetch_live_rate_from_futures() -> tuple[float, float] | None:
    """
    Fetch front-month ZQ futures price and infer current effective rate & target range.
    """
    today = date.today()
    try:
        price = get_futures_price(today.year, today.month)
        implied_rate = round(100.0 - price, 3)
        # Fed target ranges are 25bp wide, centered around multiples of 0.125%
        # e.g., 3.625 -> (3.50, 3.75)
        lower = round(round((implied_rate - 0.125) * 4) / 4, 2)
        upper = round(lower + 0.25, 2)
        return lower, upper
    except Exception:
        pass
    return None


# ── SQLite Cache ─────────────────────────────────────────────────────────────

def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fed_target_rate (
            id          INTEGER PRIMARY KEY,
            fetched_date TEXT NOT NULL,
            lower_bound  REAL NOT NULL,
            upper_bound  REAL NOT NULL
        )
    """)


def _save_to_cache(db_path: Path, lower: float, upper: float) -> None:
    conn = sqlite3.connect(db_path)
    _ensure_table(conn)
    conn.execute("DELETE FROM fed_target_rate")
    conn.execute(
        "INSERT INTO fed_target_rate (fetched_date, lower_bound, upper_bound) VALUES (?,?,?)",
        (date.today().isoformat(), lower, upper),
    )
    conn.commit()
    conn.close()


def _load_from_cache(db_path: Path) -> tuple[float, float] | None:
    try:
        conn = sqlite3.connect(db_path)
        _ensure_table(conn)
        row = conn.execute(
            "SELECT lower_bound, upper_bound FROM fed_target_rate ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn.close()
        if row:
            return row[0], row[1]
    except Exception:
        pass
    return None


# ── Public API ───────────────────────────────────────────────────────────────

def get_current_target_range(db_path: Path | None = None) -> tuple[float, float]:
    from fedwatch.db import DEFAULT_DB
    db = db_path or DEFAULT_DB

    result = fetch_live_rate_from_futures()
    if result is not None:
        _save_to_cache(db, *result)
        return result

    cached = _load_from_cache(db)
    if cached is not None:
        return cached

    return _HARDCODED_LOWER, _HARDCODED_UPPER


def get_current_midpoint(db_path: Path | None = None) -> float:
    lower, upper = get_current_target_range(db_path)
    return round((lower + upper) / 2, 4)


def get_current_target_range_str(db_path: Path | None = None) -> str:
    lower, upper = get_current_target_range(db_path)
    return f"{lower:.2f}% – {upper:.2f}%"
