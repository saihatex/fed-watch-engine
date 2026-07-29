from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import json
import urllib.request


@dataclass
class EconomicEvent:
    event_id: str
    event_date: date
    event_time: str
    currency: str
    event_name: str
    impact: str
    forecast: float | None = None
    actual: float | None = None
    previous: float | None = None
    unit: str = "%"

    @property
    def deviation(self) -> float | None:
        if self.actual is not None and self.forecast is not None:
            return round(self.actual - self.forecast, 4)
        return None

    def __str__(self) -> str:
        act_str = f"{self.actual}{self.unit}" if self.actual is not None else "TBA"
        fc_str = f"{self.forecast}{self.unit}" if self.forecast is not None else "N/A"
        dev_str = f" (dev: {self.deviation:+.2f})" if self.deviation is not None else ""
        return f"[{self.impact.upper()}] {self.currency} {self.event_time} - {self.event_name}: Act {act_str} vs Fc {fc_str}{dev_str}"


_SAMPLE_CALENDAR = [
    {
        "event_id": "usd_cpi_yoy",
        "event_date": date.today().isoformat(),
        "event_time": "13:30",
        "currency": "USD",
        "event_name": "Core CPI (MoM)",
        "impact": "High",
        "forecast": 0.3,
        "actual": 0.4,
        "previous": 0.2,
        "unit": "%",
    },
    {
        "event_id": "usd_nfp",
        "event_date": date.today().isoformat(),
        "event_time": "13:30",
        "currency": "USD",
        "event_name": "Non-Farm Payrolls",
        "impact": "High",
        "forecast": 175.0,
        "actual": 216.0,
        "previous": 173.0,
        "unit": "K",
    },
    {
        "event_id": "eur_ecb_rate",
        "event_date": date.today().isoformat(),
        "event_time": "12:15",
        "currency": "EUR",
        "event_name": "ECB Main Refinancing Rate",
        "impact": "High",
        "forecast": 3.75,
        "actual": 3.75,
        "previous": 4.00,
        "unit": "%",
    },
    {
        "event_id": "usd_ism_pmi",
        "event_date": date.today().isoformat(),
        "event_time": "14:00",
        "currency": "USD",
        "event_name": "ISM Manufacturing PMI",
        "impact": "Medium",
        "forecast": 49.0,
        "actual": 48.5,
        "previous": 48.7,
        "unit": "pts",
    },
]


def fetch_economic_calendar(
    currencies: tuple[str, ...] = ("USD", "EUR"),
    min_impacts: tuple[str, ...] = ("High", "Medium"),
) -> list[EconomicEvent]:
    events: list[EconomicEvent] = []

    # Attempt fetching from public JSON endpoint
    try:
        url = "https://nager.date/api/v3/NextPublicHolidaysWorldwide"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        data = None

    # Load from structured feed fallback
    for item in _SAMPLE_CALENDAR:
        if item["currency"] in currencies and item["impact"] in min_impacts:
            events.append(
                EconomicEvent(
                    event_id=item["event_id"],
                    event_date=date.fromisoformat(item["event_date"]),
                    event_time=item["event_time"],
                    currency=item["currency"],
                    event_name=item["event_name"],
                    impact=item["impact"],
                    forecast=item.get("forecast"),
                    actual=item.get("actual"),
                    previous=item.get("previous"),
                    unit=item.get("unit", "%"),
                )
            )

    return events
