from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import json
import re
import urllib.request
from bs4 import BeautifulSoup


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

    @property
    def status(self) -> str:
        if self.actual is not None and self.forecast is not None:
            return "Verified"
        if self.forecast is not None:
            return "Pending"
        return "N/A"

    def __str__(self) -> str:
        act_str = f"{self.actual}{self.unit}" if self.actual is not None else "TBA"
        fc_str = f"{self.forecast}{self.unit}" if self.forecast is not None else "N/A"
        dev_str = f" (dev: {self.deviation:+.2f})" if self.deviation is not None else ""
        return f"[{self.impact.upper()}] {self.currency} {self.event_date} {self.event_time} - {self.event_name}: Act {act_str} vs Fc {fc_str}{dev_str} [{self.status}]"


def _parse_num(val_str: str) -> tuple[float | None, str]:
    if not val_str or val_str.strip() in ("", "N/A", "TBA"):
        return None, "%"
    s = val_str.strip()
    unit = "%"
    if s.endswith("%"):
        unit = "%"
        s = s[:-1]
    elif s.endswith("K"):
        unit = "K"
        s = s[:-1]
    elif s.endswith("M"):
        unit = "M"
        s = s[:-1]
    elif s.endswith("B"):
        unit = "B"
        s = s[:-1]
    elif "pts" in s.lower():
        unit = "pts"
        s = re.sub(r"(?i)pts", "", s)

    s = s.replace(",", "").strip()
    try:
        return float(s), unit
    except ValueError:
        return None, "%"


def _slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[-\s]+", "_", slug)


def _month_param(target_month: date) -> str:
    return f"{target_month.strftime('%b').lower()}.{target_month.year}"


def _months_in_range(start: date, end: date) -> list[date]:
    months: list[date] = []
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        months.append(date(y, m, 1))
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1
    return months


def scrape_forexfactory_calendar(target_month: date) -> list[EconomicEvent]:
    month_param = _month_param(target_month)
    url = f"https://www.forexfactory.com/calendar?month={month_param}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    req = urllib.request.Request(url, headers=headers)

    with urllib.request.urlopen(req, timeout=6) as resp:
        html = resp.read().decode("utf-8")

    soup = BeautifulSoup(html, "html.parser")
    rows = soup.find_all("tr", class_=re.compile(r"calendar__row"))

    events: list[EconomicEvent] = []
    current_date_str = ""
    parse_year = target_month.year

    for row in rows:
        date_td = row.find("td", class_=re.compile(r"calendar__date"))
        if date_td and date_td.text.strip():
            current_date_str = date_td.text.strip()

        currency_td = row.find("td", class_=re.compile(r"calendar__currency"))
        event_td = row.find("td", class_=re.compile(r"calendar__event"))
        impact_td = row.find("td", class_=re.compile(r"calendar__impact"))
        actual_td = row.find("td", class_=re.compile(r"calendar__actual"))
        forecast_td = row.find("td", class_=re.compile(r"calendar__forecast"))
        previous_td = row.find("td", class_=re.compile(r"calendar__previous"))
        time_td = row.find("td", class_=re.compile(r"calendar__time"))

        ccy = currency_td.text.strip() if currency_td else ""
        title = event_td.text.strip() if event_td else ""
        if not ccy or not title or not current_date_str:
            continue

        impact = "Low"
        if impact_td:
            span = impact_td.find("span")
            if span:
                classes = " ".join(span.get("class", []))
                if "impact-red" in classes:
                    impact = "High"
                elif "impact-ora" in classes:
                    impact = "Medium"
                elif "impact-yel" in classes:
                    impact = "Low"

        act_raw = actual_td.text.strip() if actual_td else ""
        fc_raw = forecast_td.text.strip() if forecast_td else ""
        prev_raw = previous_td.text.strip() if previous_td else ""
        tm = time_td.text.strip() if time_td else ""

        try:
            ev_date = datetime.strptime(f"{parse_year} {current_date_str}", "%Y %a %b %d").date()
        except ValueError:
            continue

        act_val, act_unit = _parse_num(act_raw)
        fc_val, fc_unit = _parse_num(fc_raw)
        prev_val, prev_unit = _parse_num(prev_raw)
        unit = act_unit or fc_unit or prev_unit

        event_id = f"{ccy.lower()}_{_slugify(title)}_{ev_date.isoformat()}"

        events.append(
            EconomicEvent(
                event_id=event_id,
                event_date=ev_date,
                event_time=tm or "All Day",
                currency=ccy,
                event_name=title,
                impact=impact,
                forecast=fc_val,
                actual=act_val,
                previous=prev_val,
                unit=unit,
            )
        )

    return events


def _scrape_months(months: list[date]) -> tuple[list[EconomicEvent], list[str]]:
    scraped: list[EconomicEvent] = []
    scraped_labels: list[str] = []
    seen_ids: set[str] = set()

    for month in months:
        label = _month_param(month)
        try:
            month_events = scrape_forexfactory_calendar(month)
        except Exception:
            continue
        scraped_labels.append(label)
        for ev in month_events:
            if ev.event_id not in seen_ids:
                seen_ids.add(ev.event_id)
                scraped.append(ev)

    return scraped, scraped_labels


def fetch_economic_calendar(
    days_ahead: int = 0,
    start_date: date | None = None,
    currencies: tuple[str, ...] = ("USD", "EUR"),
    min_impacts: tuple[str, ...] = ("High", "Medium"),
) -> tuple[list[EconomicEvent], str]:
    today = start_date or date.today()
    end_date = today + timedelta(days=days_ahead)
    months = _months_in_range(today, end_date)

    scraped_events, scraped_labels = _scrape_months(months)

    if scraped_labels:
        months_str = ", ".join(scraped_labels)
        source_label = (
            f"ForexFactory | scraped: {months_str} | "
            f"window: {today.isoformat()}..{end_date.isoformat()}"
        )
    else:
        scraped_events = []
        source_label = "sample data"

    if not scraped_events:
        scraped_events = [
            EconomicEvent(
                event_id="usd_cpi_yoy",
                event_date=today,
                event_time="13:30",
                currency="USD",
                event_name="Core CPI (MoM)",
                impact="High",
                forecast=0.3,
                actual=0.4,
                previous=0.2,
                unit="%",
            ),
            EconomicEvent(
                event_id="usd_nfp",
                event_date=today,
                event_time="13:30",
                currency="USD",
                event_name="Non-Farm Payrolls",
                impact="High",
                forecast=175.0,
                actual=216.0,
                previous=173.0,
                unit="K",
            ),
            EconomicEvent(
                event_id="eur_ecb_rate",
                event_date=today,
                event_time="12:15",
                currency="EUR",
                event_name="ECB Main Refinancing Rate",
                impact="High",
                forecast=3.75,
                actual=3.75,
                previous=4.00,
                unit="%",
            ),
            EconomicEvent(
                event_id="usd_ism_pmi",
                event_date=today,
                event_time="14:00",
                currency="USD",
                event_name="ISM Manufacturing PMI",
                impact="Medium",
                forecast=49.0,
                actual=48.5,
                previous=48.7,
                unit="pts",
            ),
        ]

    events: list[EconomicEvent] = []

    for ev in scraped_events:
        if today <= ev.event_date <= end_date:
            if ev.currency in currencies and ev.impact in min_impacts:
                events.append(ev)

    if scraped_labels and not events:
        source_label += " | no events matched filter"

    return events, source_label
