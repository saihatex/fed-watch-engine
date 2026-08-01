from datetime import date
from unittest.mock import patch

from fedwatch.news_loader import (
    EconomicEvent,
    _month_param,
    _months_in_range,
    fetch_economic_calendar,
)


def test_month_param():
    assert _month_param(date(2026, 8, 1)) == "aug.2026"
    assert _month_param(date(2026, 1, 15)) == "jan.2026"


def test_months_in_range_single_month():
    start = date(2026, 8, 1)
    end = date(2026, 8, 31)
    assert _months_in_range(start, end) == [date(2026, 8, 1)]


def test_months_in_range_crosses_month_boundary():
    start = date(2026, 7, 30)
    end = date(2026, 8, 30)
    assert _months_in_range(start, end) == [date(2026, 7, 1), date(2026, 8, 1)]


def test_months_in_range_crosses_year():
    start = date(2025, 12, 20)
    end = date(2026, 1, 10)
    assert _months_in_range(start, end) == [date(2025, 12, 1), date(2026, 1, 1)]


def test_fetch_scrapes_all_months_in_window():
    def fake_scrape(target_month: date):
        day = 31 if target_month.month == 7 else 5
        return [
            EconomicEvent(
                event_id=f"usd_evt_{target_month.month}",
                event_date=date(target_month.year, target_month.month, day),
                event_time="13:30",
                currency="USD",
                event_name="Test Event",
                impact="High",
            )
        ]

    with patch("fedwatch.news_loader.scrape_forexfactory_calendar", side_effect=fake_scrape):
        events, source = fetch_economic_calendar(
            days_ahead=30,
            start_date=date(2026, 7, 30),
        )

    assert len(events) == 2
    assert "jul.2026" in source
    assert "aug.2026" in source
    assert "2026-07-30..2026-08-29" in source
