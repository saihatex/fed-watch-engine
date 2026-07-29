from fedwatch import (
    next_meeting,
    get_futures_price_for_meeting,
    rate_move_probability,
    CURRENT_TARGET_MIDPOINT,
    CURRENT_TARGET_RANGE,
)


def main():
    meeting = next_meeting()
    print(f"Next FOMC meeting: {meeting.decision_date}")
    print(f"Current target range: {CURRENT_TARGET_RANGE[0]:.2f}-{CURRENT_TARGET_RANGE[1]:.2f}%\n")

    try:
        price = get_futures_price_for_meeting(meeting.decision_date)
        source = "yfinance (live)"
    except Exception as e:
        print(f"Live fetch failed ({e}); using fallback price.\n")
        price = 96.38
        source = "manual fallback"

    result = rate_move_probability(
        futures_price=price,
        decision_date=meeting.decision_date,
        current_rate=CURRENT_TARGET_MIDPOINT,
    )

    print(f"Source: {source}")
    print(result)
    print(f"\nImplied post-meeting rate: {result.implied_rate_after:.3f}%")


if __name__ == "__main__":
    main()
