from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

_CONFIRMED_LOWER = 3.50
_CONFIRMED_UPPER = 3.75


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


def get_current_target_range(db_path: Path | None = None) -> tuple[float, float]:
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
