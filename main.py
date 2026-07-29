from __future__ import annotations

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


def _prompt(msg: str) -> str:
    try:
        return input(msg).strip()
    except (EOFError, KeyboardInterrupt):
        return "0"


def _load_bootstrap(months: int = 8):
    print("Fetching ZQ futures chain...", end=" ", flush=True)
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
    print("done.")
    return nodes


def _level3(idx: int, events: list, nodes, db_path):
    from fedwatch.db import DEFAULT_DB
    from fedwatch.db import load_events_in_range
    from datetime import date

    ev = events[idx - 1]
    today = date.today()
    start = today - timedelta(days=120)
    history = load_events_in_range(start, today)

    while True:
        print(render_event_deep_dive(idx, ev, nodes, history))
        cmd = _prompt(">> ").upper()
        if cmd == "B" or cmd == "":
            break


def _level2(days_ahead: int, window_title: str, nodes):
    from fedwatch.db import DEFAULT_DB
    from datetime import date

    today = date.today()

    print("Fetching economic calendar...", end=" ", flush=True)
    events, source = fetch_economic_calendar(days_ahead=days_ahead)
    save_economic_events(events)
    print(f"found {len(events)} events.")

    sentiment = analyze_sentiment(nodes, events)
    delta_lines = format_delta_report(nodes)

    while True:
        print(render_event_table(events, window_title, source))
        print(render_sentiment_block(sentiment, delta_lines))

        cmd = _prompt(">> ").upper()

        if cmd == "B" or cmd == "":
            return
        elif cmd == "G":
            print("Opening Plotly Fed Path chart in browser...")
            fig = create_fed_path_figure(nodes, CURRENT_TARGET_MIDPOINT)
            fig.show()
        elif cmd.isdigit():
            idx = int(cmd)
            if 1 <= idx <= len(events):
                _level3(idx, events, nodes, None)
            else:
                print(f"  Invalid event number. Enter 1-{len(events)}.")
        else:
            print("  Unknown command.")


def _level1(nodes):
    while True:
        print("\n=================================================================")
        print(" FED WATCH ENGINE")
        print("=================================================================")
        print(" [1] Today    [2] Week (+7 days)    [3] Month (+30 days)    [0] Exit")
        print("-----------------------------------------------------------------")

        cmd = _prompt(">> ")

        if cmd == "0" or cmd.upper() == "Q":
            print("Goodbye.")
            sys.exit(0)
        elif cmd in _WINDOW_OPTS:
            days_ahead, window_title = _WINDOW_OPTS[cmd]
            persist_bootstrap_nodes(nodes)
            _level2(days_ahead, window_title, nodes)
        else:
            print("  Enter 1, 2, 3 or 0.")


def main():
    nodes = _load_bootstrap()
    print(render_fomc_path_block(nodes, CURRENT_TARGET_MIDPOINT))
    _level1(nodes)


if __name__ == "__main__":
    main()
