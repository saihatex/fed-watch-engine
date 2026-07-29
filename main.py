from __future__ import annotations

import os
import sys
from datetime import date, timedelta

from fedwatch import (
    analyze_sentiment,
    create_event_history_figure,
    create_fed_path_figure,
    fetch_economic_calendar,
    format_delta_report,
    get_current_midpoint,
    get_full_chain,
    load_events_in_range,
    persist_bootstrap_nodes,
    render_event_deep_dive,
    render_event_table,
    render_fomc_path_block,
    render_sentiment_block,
    run_bootstrap,
    save_economic_events,
    seed_historical_macro_data,
)


_WINDOW_OPTS = {"1": (0, "Today"), "2": (7, "Week"), "3": (30, "Month")}


def _clr():
    os.system("cls" if os.name == "nt" else "clear")


def _prompt(msg: str = ">> ") -> str:
    try:
        return input(msg).strip()
    except (EOFError, KeyboardInterrupt):
        return "0"


def _header():
    print("=================================================================")
    print(" WATCH ENGINE v2.2")
    print("=================================================================")


def _load_bootstrap(months: int = 8):
    print(" Loading futures data...", end=" ", flush=True)
    initial_rate = get_current_midpoint()
    chain = get_full_chain(months_ahead=months)

    if not chain:
        print("\n  [WARNING] No live ZQ futures data retrieved from exchange/Yahoo Finance.")
        print("            Rate path bootstrap cannot be calculated without market quotes.\n")
        nodes = []
    else:
        nodes = run_bootstrap(futures_chain=chain, initial_rate=initial_rate)
        persist_bootstrap_nodes(nodes)
        print("done.")

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
        print(render_event_deep_dive(idx, ev, nodes, history))

        if is_rate_event and nodes:
            print()
            print(render_fomc_path_block(nodes, initial_rate))

        print()
        cmd = _prompt().upper()
        if cmd == "B" or cmd == "":
            return
        elif cmd == "G":
            if is_rate_event:
                if not nodes:
                    input(" No futures curve data available for chart. Press Enter.")
                else:
                    print(" Opening Rate Curve chart in browser...")
                    fig = create_fed_path_figure(nodes, initial_rate)
                    fig.show()
            else:
                print(f" Opening Actual vs Forecast chart for {ev.event_name}...")
                fig = create_event_history_figure(ev.event_name, history)
                fig.show()


def _screen_news_list(days_ahead: int, window_title: str, nodes, initial_rate: float):
    print(" Fetching calendar...", end=" ", flush=True)
    events, source = fetch_economic_calendar(days_ahead=days_ahead)
    save_economic_events(events)
    print(f"found {len(events)} events.")

    while True:
        _clr()
        _header()
        print(render_event_table(events, window_title, source))
        print()

        cmd = _prompt().upper()

        if cmd == "B" or cmd == "":
            return
        elif cmd == "G":
            if not nodes:
                input(" No futures curve data available for chart. Press Enter.")
            else:
                print(" Opening Fed Path Rate Curve in browser...")
                fig = create_fed_path_figure(nodes, initial_rate)
                fig.show()
        elif cmd.isdigit():
            idx = int(cmd)
            if 1 <= idx <= len(events):
                _screen_deep_dive(idx, events, nodes, initial_rate)
            else:
                input(" Invalid number. Press Enter.")
        else:
            input(" Unknown command. Press Enter.")


def _screen_main_menu():
    seed_historical_macro_data()

    nodes = None
    initial_rate = 3.625

    while True:
        _clr()
        _header()
        print(" [1] Today    [2] Week (+7 days)    [3] Month (+30 days)    [0] Exit")
        print("-----------------------------------------------------------------")
        cmd = _prompt()

        if cmd == "0" or cmd.upper() == "Q":
            _clr()
            print("Goodbye.")
            sys.exit(0)
        elif cmd in _WINDOW_OPTS:
            if nodes is None:
                _clr()
                _header()
                nodes, initial_rate = _load_bootstrap()
            days_ahead, window_title = _WINDOW_OPTS[cmd]
            _screen_news_list(days_ahead, window_title, nodes, initial_rate)
        else:
            input(" Enter 1, 2, 3 or 0. Press Enter.")


def main():
    _screen_main_menu()


if __name__ == "__main__":
    main()
