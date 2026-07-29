from __future__ import annotations

import argparse
from datetime import date

from fedwatch import (
    CURRENT_TARGET_MIDPOINT,
    CURRENT_TARGET_RANGE,
    format_delta_report,
    get_full_chain,
    persist_bootstrap_nodes,
    render_terminal_summary,
    run_bootstrap,
)
from fedwatch.dashboard import create_fed_path_figure


def main():
    parser = argparse.ArgumentParser(description="Fed Watch Engine — Market-implied FOMC rate path")
    parser.add_argument("--months", type=int, default=8, help="Number of months ahead to analyze (default: 8)")
    parser.add_argument("--plot", action="store_true", help="Show interactive Plotly Fed Path chart")
    parser.add_argument("--no-db", action="store_true", help="Disable SQLite snapshot saving")
    args = parser.parse_args()

    print(f"Fetching ZQ futures chain for {args.months} months ahead...\n")
    chain = get_full_chain(months_ahead=args.months)

    if not chain:
        print("[fallback] Live futures chain fetch failed or returned empty; generating fallback chain.\n")
        today = date.today()
        cur_y, cur_m = today.year, today.month
        chain = {}
        for i in range(args.months):
            chain[(cur_y, cur_m)] = 96.25 - (i * 0.05)
            cur_m += 1
            if cur_m > 12:
                cur_m = 1
                cur_y += 1

    nodes = run_bootstrap(futures_chain=chain, initial_rate=CURRENT_TARGET_MIDPOINT)

    if not args.no_db:
        persist_bootstrap_nodes(nodes)

    print(render_terminal_summary(nodes, CURRENT_TARGET_MIDPOINT))

    if not args.no_db:
        print("\nDAILY DELTA REPORT (VS PREVIOUS SNAPSHOT):")
        delta_lines = format_delta_report(nodes)
        for line in delta_lines:
            print(f"  * {line}")

    if args.plot:
        fig = create_fed_path_figure(nodes, CURRENT_TARGET_MIDPOINT)
        fig.show()


if __name__ == "__main__":
    main()
