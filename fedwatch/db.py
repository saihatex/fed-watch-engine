from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

from fedwatch.news_loader import EconomicEvent

DEFAULT_DB = Path(__file__).parent.parent / "fedwatch.db"


def init_db(db_path: Path = DEFAULT_DB) -> None:
    with sqlite3.connect(db_path) as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS fomc_meetings (
                decision_date TEXT PRIMARY KEY,
                has_sep       INTEGER NOT NULL DEFAULT 0,
                rate_before   REAL,
                rate_after    REAL
            );

            CREATE TABLE IF NOT EXISTS daily_snapshots (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_date TEXT NOT NULL,
                decision_date TEXT NOT NULL,
                futures_price REAL,
                implied_rate  REAL,
                prob_cut50    REAL,
                prob_cut25    REAL,
                prob_hold     REAL,
                prob_hike25   REAL,
                prob_hike50   REAL,
                UNIQUE(snapshot_date, decision_date)
            );

            CREATE TABLE IF NOT EXISTS fomc_events (
                decision_date  TEXT PRIMARY KEY,
                rate_before    REAL NOT NULL,
                rate_after     REAL NOT NULL,
                actual_move_bp INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS economic_events (
                event_id     TEXT PRIMARY KEY,
                event_date   TEXT NOT NULL,
                event_time   TEXT,
                currency     TEXT NOT NULL,
                event_name   TEXT NOT NULL,
                impact       TEXT NOT NULL,
                forecast     REAL,
                actual       REAL,
                previous     REAL,
                unit         TEXT,
                deviation    REAL
            );
        """)


def save_snapshot(
    snapshot_date: date,
    decision_date: date,
    futures_price: float,
    implied_rate: float,
    probs: dict[int, float],
    db_path: Path = DEFAULT_DB,
) -> None:
    with sqlite3.connect(db_path) as con:
        con.execute(
            """
            INSERT INTO daily_snapshots
                (snapshot_date, decision_date, futures_price, implied_rate,
                 prob_cut50, prob_cut25, prob_hold, prob_hike25, prob_hike50)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(snapshot_date, decision_date) DO UPDATE SET
                futures_price = excluded.futures_price,
                implied_rate  = excluded.implied_rate,
                prob_cut50    = excluded.prob_cut50,
                prob_cut25    = excluded.prob_cut25,
                prob_hold     = excluded.prob_hold,
                prob_hike25   = excluded.prob_hike25,
                prob_hike50   = excluded.prob_hike50
            """,
            (
                snapshot_date.isoformat(),
                decision_date.isoformat(),
                futures_price,
                implied_rate,
                probs.get(-50, 0.0),
                probs.get(-25, 0.0),
                probs.get(0, 0.0),
                probs.get(25, 0.0),
                probs.get(50, 0.0),
            ),
        )


def load_snapshots_for_meeting(
    decision_date: date,
    db_path: Path = DEFAULT_DB,
) -> list[dict]:
    with sqlite3.connect(db_path) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT * FROM daily_snapshots WHERE decision_date = ? ORDER BY snapshot_date",
            (decision_date.isoformat(),),
        ).fetchall()
    return [dict(r) for r in rows]


def load_yesterday(
    today: date,
    decision_date: date,
    db_path: Path = DEFAULT_DB,
) -> dict | None:
    with sqlite3.connect(db_path) as con:
        con.row_factory = sqlite3.Row
        row = con.execute(
            """
            SELECT * FROM daily_snapshots
            WHERE decision_date = ?
              AND snapshot_date < ?
            ORDER BY snapshot_date DESC
            LIMIT 1
            """,
            (decision_date.isoformat(), today.isoformat()),
        ).fetchone()
    return dict(row) if row else None


def record_fomc_event(
    decision_date: date,
    rate_before: float,
    rate_after: float,
    actual_move_bp: int,
    db_path: Path = DEFAULT_DB,
) -> None:
    with sqlite3.connect(db_path) as con:
        con.execute(
            """
            INSERT OR REPLACE INTO fomc_events
                (decision_date, rate_before, rate_after, actual_move_bp)
            VALUES (?, ?, ?, ?)
            """,
            (decision_date.isoformat(), rate_before, rate_after, actual_move_bp),
        )


def save_economic_events(
    events: list[EconomicEvent],
    db_path: Path = DEFAULT_DB,
) -> None:
    init_db(db_path)
    with sqlite3.connect(db_path) as con:
        for ev in events:
            con.execute(
                """
                INSERT OR REPLACE INTO economic_events
                    (event_id, event_date, event_time, currency, event_name, impact, forecast, actual, previous, unit, deviation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ev.event_id,
                    ev.event_date.isoformat(),
                    ev.event_time,
                    ev.currency,
                    ev.event_name,
                    ev.impact,
                    ev.forecast,
                    ev.actual,
                    ev.previous,
                    ev.unit,
                    ev.deviation,
                ),
            )


def load_today_events(
    today: date | None = None,
    db_path: Path = DEFAULT_DB,
) -> list[dict]:
    init_db(db_path)
    target_date = (today or date.today()).isoformat()
    with sqlite3.connect(db_path) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT * FROM economic_events WHERE event_date = ? ORDER BY event_time",
            (target_date,),
        ).fetchall()
    return [dict(r) for r in rows]
