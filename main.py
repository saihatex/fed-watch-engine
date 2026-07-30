from __future__ import annotations

import os
import sys
from datetime import date, timedelta

from rich.console import Console
from rich.panel import Panel

from fedwatch import (
    create_event_history_figure,
    create_fed_path_figure,
    fetch_economic_calendar,
    get_current_midpoint,
    get_full_chain,
    load_events_in_range,
    persist_bootstrap_nodes,
    render_event_deep_dive,
    render_event_table,
    render_fomc_path_block,
    run_bootstrap,
    save_economic_events,
)

console = Console(width=95)

_WINDOW_OPTS = {"1": (0, "Today"), "2": (7, "Week"), "3": (30, "Month")}


def _clr():
    os.system("cls" if os.name == "nt" else "clear")


def _prompt(msg: str = "> ") -> str:
    try:
        return input(msg).strip()
    except (EOFError, KeyboardInterrupt):
        return "0"


def _header():
    console.print(Panel("Macro Watch", border_style="white"))


def _load_bootstrap(months: int = 8):
    console.print("Loading ZQ futures...", end=" ")
    console.file.flush()
    initial_rate = get_current_midpoint()
    chain = get_full_chain(months_ahead=months)

    if not chain:
        console.print("\nNo ZQ data. Rate path unavailable.\n")
        nodes = []
    else:
        nodes = run_bootstrap(futures_chain=chain, initial_rate=initial_rate)
        persist_bootstrap_nodes(nodes)
        console.print("ok")

    return nodes, initial_rate


def _screen_deep_dive(idx: int, events: list, nodes, initial_rate: float):
    ev = events[idx - 1]
    today = date.today()
    start = today - timedelta(days=365)
    history = load_events_in_range(start, today)

    is_rate_event = "Rate" in ev.event_name or "FOMC" in ev.event_name or "Federal Funds" in ev.event_name

    while True:
        _clr()
        _header()
        console.print(render_event_deep_dive(idx, ev, nodes, history))

        if is_rate_event and nodes:
            console.print()
            console.print(render_fomc_path_block(nodes, initial_rate))

        console.print()
        cmd = _prompt().upper()
        if cmd in ("B", ""):
            return
        if cmd == "G":
            if is_rate_event:
                if not nodes:
                    input("No futures data. Enter.")
                else:
                    create_fed_path_figure(nodes, initial_rate).show()
            else:
                create_event_history_figure(ev.event_name, history).show()


def _screen_news_list(days_ahead: int, window_title: str, nodes, initial_rate: float):
    console.print("Fetching calendar...", end=" ")
    console.file.flush()
    events, source = fetch_economic_calendar(days_ahead=days_ahead)
    save_economic_events(events)
    console.print(f"{len(events)} events")

    while True:
        _clr()
        _header()
        console.print(render_event_table(events, window_title, source))
        console.print()

        cmd = _prompt().upper()

        if cmd in ("B", ""):
            return
        if cmd == "G":
            if not nodes:
                input("No futures data. Enter.")
            else:
                create_fed_path_figure(nodes, initial_rate).show()
        elif cmd.isdigit():
            idx = int(cmd)
            if 1 <= idx <= len(events):
                _screen_deep_dive(idx, events, nodes, initial_rate)
            else:
                input("Invalid. Enter.")
        else:
            input("Unknown command. Enter.")


def _screen_main_menu():
    nodes = None
    initial_rate = 3.625

    while True:
        _clr()
        _header()
        console.print(Panel(
            "[1] Today\n[2] Week\n[3] Month\n[0] Exit",
            title="Menu",
            border_style="white",
        ))
        cmd = _prompt()

        if cmd in ("0", "q", "Q"):
            _clr()
            sys.exit(0)
        if cmd in _WINDOW_OPTS:
            if nodes is None:
                _clr()
                _header()
                nodes, initial_rate = _load_bootstrap()
            days_ahead, window_title = _WINDOW_OPTS[cmd]
            _screen_news_list(days_ahead, window_title, nodes, initial_rate)
        else:
            input("Enter 1, 2, 3 or 0. ")


def main():
    _screen_main_menu()


if __name__ == "__main__":
    main()
