from __future__ import annotations

import os
import sys
from datetime import date, timedelta

from fedwatch import (
    CURRENT_TARGET_MIDPOINT,
    analyze_sentiment,
    fetch_economic_calendar,
    format_delta_report,
    get_full_chain,
    load_events_in_range,
    persist_bootstrap_nodes,
    render_event_deep_dive,
    render_event_table,
    render_fomc_path_block,
    render_sentiment_block,
    run_bootstrap,
    save_economic_events,
)
from fedwatch.dashboard import create_fed_path_figure


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
    print(" WATCH ENGINE v2.1")
    print("=================================================================")


def _load_bootstrap(months: int = 8):
    print(" Loading futures data...", end=" ", flush=True)
    chain = get_full_chain(months_ahead=months)
    if not chain:
        today = date.today()
        y, m = today.year, today.month
        chain = {}
        for i in range(months):
            chain[(y, m)] = 96.25 - i * 0.05
            m += 1
            if m > 12:
                m = 1
                y += 1
    nodes = run_bootstrap(futures_chain=chain, initial_rate=CURRENT_TARGET_MIDPOINT)
    persist_bootstrap_nodes(nodes)
    print("done.")
    return nodes


def _screen_deep_dive(idx: int, events: list, nodes):
    ev = events[idx - 1]
    today = date.today()
    history = load_events_in_range(today - timedelta(days=120), today)
    sentiment = analyze_sentiment(nodes, [ev])
    delta_lines = format_delta_report(nodes)

    while True:
        _clr()
        _header()
        print(render_event_deep_dive(idx, ev, nodes, history))
        print()
        print(render_fomc_path_block(nodes, CURRENT_TARGET_MIDPOINT))
        print()
        print(render_sentiment_block(sentiment, delta_lines))
        print()
        print(" G = Open Fed Path chart   |   B = Back to news list")
        print("-----------------------------------------------------------------")
        cmd = _prompt().upper()
        if cmd == "B" or cmd == "":
            return
        elif cmd == "G":
            print(" Opening chart in browser...")
            fig = create_fed_path_figure(nodes, CURRENT_TARGET_MIDPOINT)
            fig.show()


def _screen_news_list(days_ahead: int, window_title: str, nodes):
    print(" Fetching calendar...", end=" ", flush=True)
    events, source = fetch_economic_calendar(days_ahead=days_ahead)
    save_economic_events(events)
    source_short = "ForexFactory"
    print(f"found {len(events)} events.")

    while True:
        _clr()
        _header()
        print(render_event_table(events, window_title, source_short))
        print()

        cmd = _prompt().upper()

        if cmd == "B" or cmd == "":
            return
        elif cmd == "G":
            print(" Opening chart in browser...")
            fig = create_fed_path_figure(nodes, CURRENT_TARGET_MIDPOINT)
            fig.show()
        elif cmd.isdigit():
            idx = int(cmd)
            if 1 <= idx <= len(events):
                _screen_deep_dive(idx, events, nodes)
            else:
                input(f" Invalid number. Press Enter.")
        else:
            input(" Unknown command. Press Enter.")


def _screen_main_menu():
    nodes = None

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
                nodes = _load_bootstrap()
            days_ahead, window_title = _WINDOW_OPTS[cmd]
            _screen_news_list(days_ahead, window_title, nodes)
        else:
            input(" Enter 1, 2, 3 or 0. Press Enter.")


def main():
    _screen_main_menu()


if __name__ == "__main__":
    main()
