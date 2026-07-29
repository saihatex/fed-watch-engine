from __future__ import annotations

import argparse
from datetime import date

from fedwatch import (
    CURRENT_TARGET_MIDPOINT,
    analyze_macro_bias,
    fetch_economic_calendar,
    format_delta_report,
    get_full_chain,
    persist_bootstrap_nodes,
    render_macro_news_block,
    render_script_thoughts_block,
    render_terminal_summary,
    run_bootstrap,
    save_economic_events,
)
from fedwatch.dashboard import create_fed_path_figure


def main():
    parser = argparse.ArgumentParser(description="Fed Watch Engine — Macro Terminal & SMC Playbook")
    parser.add_argument("--months", type=int, default=8, help="Number of months ahead to analyze (default: 8)")
    parser.add_argument("--plot", action="store_true", help="Show interactive Plotly Fed Path chart")
    parser.add_argument("--no-db", action="store_true", help="Disable SQLite snapshot saving")
    args = parser.parse_args()

    print(f"Fetching ZQ futures chain for {args.months} months ahead...")
    chain = get_full_chain(months_ahead=args.months)

    if not chain:
        print("[fallback] Live futures chain fetch failed or returned empty; generating fallback chain.")
        today = date.today()
        cur_y, cur_m = today.year, today.month
        chain = {}
        for i in range(args.months):
            chain[(cur_y, cur_m)] = 96.25 - (i * 0.05)
            cur_m += 1
            if cur_m > 12:
                cur_m = 1
                cur_y += 1

    # 1. Compute Fed Funds Bootstrapped Path
    nodes = run_bootstrap(futures_chain=chain, initial_rate=CURRENT_TARGET_MIDPOINT)

    # 2. Fetch & Save Economic News Calendar
    events = fetch_economic_calendar()

    if not args.no_db:
        persist_bootstrap_nodes(nodes)
        save_economic_events(events)

    # 3. Compute Macro Bias & SMC Playbook
    bias = analyze_macro_bias(nodes, events)

    # 4. Render Terminal Blocks
    print(render_terminal_summary(nodes, CURRENT_TARGET_MIDPOINT))

    if not args.no_db:
        print("\n DAILY DELTA REPORT (VS PREVIOUS SNAPSHOT):")
        delta_lines = format_delta_report(nodes)
        for line in delta_lines:
            print(f"  * {line}")

    print(render_macro_news_block(events))
    print(render_script_thoughts_block(bias))

    if args.plot:
        fig = create_fed_path_figure(nodes, CURRENT_TARGET_MIDPOINT)
        fig.show()


if __name__ == "__main__":
    main()
