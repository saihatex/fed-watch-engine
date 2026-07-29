from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from fedwatch.db import DEFAULT_DB, init_db, save_economic_events
from fedwatch.news_loader import EconomicEvent


def seed_historical_macro_data(db_path: Path = DEFAULT_DB) -> int:
    init_db(db_path)
    today = date.today()

    historical_records = [
        # Core CPI (MoM)
        ("usd_cpi_2025_08", today - timedelta(days=345), "13:30", "USD", "Core CPI (MoM)", "High", 0.2, 0.3, 0.2, "%"),
        ("usd_cpi_2025_09", today - timedelta(days=315), "13:30", "USD", "Core CPI (MoM)", "High", 0.3, 0.3, 0.3, "%"),
        ("usd_cpi_2025_10", today - timedelta(days=285), "13:30", "USD", "Core CPI (MoM)", "High", 0.3, 0.2, 0.3, "%"),
        ("usd_cpi_2025_11", today - timedelta(days=255), "13:30", "USD", "Core CPI (MoM)", "High", 0.2, 0.3, 0.2, "%"),
        ("usd_cpi_2025_12", today - timedelta(days=225), "13:30", "USD", "Core CPI (MoM)", "High", 0.3, 0.3, 0.3, "%"),
        ("usd_cpi_2026_01", today - timedelta(days=195), "13:30", "USD", "Core CPI (MoM)", "High", 0.3, 0.4, 0.3, "%"),
        ("usd_cpi_2026_02", today - timedelta(days=165), "13:30", "USD", "Core CPI (MoM)", "High", 0.3, 0.4, 0.4, "%"),
        ("usd_cpi_2026_03", today - timedelta(days=135), "13:30", "USD", "Core CPI (MoM)", "High", 0.3, 0.3, 0.4, "%"),
        ("usd_cpi_2026_04", today - timedelta(days=105), "13:30", "USD", "Core CPI (MoM)", "High", 0.3, 0.3, 0.3, "%"),
        ("usd_cpi_2026_05", today - timedelta(days=75),  "13:30", "USD", "Core CPI (MoM)", "High", 0.3, 0.2, 0.3, "%"),
        ("usd_cpi_2026_06", today - timedelta(days=45),  "13:30", "USD", "Core CPI (MoM)", "High", 0.2, 0.2, 0.2, "%"),
        ("usd_cpi_2026_07", today - timedelta(days=15),  "13:30", "USD", "Core CPI (MoM)", "High", 0.3, 0.4, 0.2, "%"),

        # Non-Farm Payrolls
        ("usd_nfp_2025_08", today - timedelta(days=340), "13:30", "USD", "Non-Farm Payrolls", "High", 165.0, 142.0, 179.0, "K"),
        ("usd_nfp_2025_09", today - timedelta(days=310), "13:30", "USD", "Non-Farm Payrolls", "High", 170.0, 254.0, 142.0, "K"),
        ("usd_nfp_2025_10", today - timedelta(days=280), "13:30", "USD", "Non-Farm Payrolls", "High", 110.0, 12.0, 254.0, "K"),
        ("usd_nfp_2025_11", today - timedelta(days=250), "13:30", "USD", "Non-Farm Payrolls", "High", 215.0, 227.0, 12.0, "K"),
        ("usd_nfp_2025_12", today - timedelta(days=220), "13:30", "USD", "Non-Farm Payrolls", "High", 170.0, 256.0, 227.0, "K"),
        ("usd_nfp_2026_01", today - timedelta(days=190), "13:30", "USD", "Non-Farm Payrolls", "High", 185.0, 353.0, 256.0, "K"),
        ("usd_nfp_2026_02", today - timedelta(days=160), "13:30", "USD", "Non-Farm Payrolls", "High", 200.0, 275.0, 353.0, "K"),
        ("usd_nfp_2026_03", today - timedelta(days=130), "13:30", "USD", "Non-Farm Payrolls", "High", 214.0, 303.0, 275.0, "K"),
        ("usd_nfp_2026_04", today - timedelta(days=100), "13:30", "USD", "Non-Farm Payrolls", "High", 243.0, 175.0, 303.0, "K"),
        ("usd_nfp_2026_05", today - timedelta(days=70),  "13:30", "USD", "Non-Farm Payrolls", "High", 180.0, 272.0, 175.0, "K"),
        ("usd_nfp_2026_06", today - timedelta(days=40),  "13:30", "USD", "Non-Farm Payrolls", "High", 190.0, 206.0, 272.0, "K"),
        ("usd_nfp_2026_07", today - timedelta(days=10),  "13:30", "USD", "Non-Farm Payrolls", "High", 175.0, 216.0, 206.0, "K"),

        # Advance GDP q/q
        ("usd_gdp_2025_09", today - timedelta(days=305), "13:30", "USD", "Advance GDP q/q", "High", 2.8, 3.0, 1.4, "%"),
        ("usd_gdp_2025_12", today - timedelta(days=215), "13:30", "USD", "Advance GDP q/q", "High", 2.3, 2.5, 3.0, "%"),
        ("usd_gdp_2026_03", today - timedelta(days=125), "13:30", "USD", "Advance GDP q/q", "High", 1.6, 1.3, 2.5, "%"),
        ("usd_gdp_2026_06", today - timedelta(days=35),  "13:30", "USD", "Advance GDP q/q", "High", 2.0, 2.8, 1.3, "%"),

        # German Prelim CPI m/m
        ("eur_cpi_2025_09", today - timedelta(days=300), "12:00", "EUR", "German Prelim CPI m/m", "Medium", 0.3, 0.3, 0.1, "%"),
        ("eur_cpi_2025_12", today - timedelta(days=210), "12:00", "EUR", "German Prelim CPI m/m", "Medium", 0.2, 0.1, 0.3, "%"),
        ("eur_cpi_2026_03", today - timedelta(days=120), "12:00", "EUR", "German Prelim CPI m/m", "Medium", 0.4, 0.4, 0.2, "%"),
        ("eur_cpi_2026_06", today - timedelta(days=30),  "12:00", "EUR", "German Prelim CPI m/m", "Medium", 0.1, 0.1, 0.4, "%"),
    ]

    events = [
        EconomicEvent(
            event_id=item[0],
            event_date=item[1],
            event_time=item[2],
            currency=item[3],
            event_name=item[4],
            impact=item[5],
            forecast=item[6],
            actual=item[7],
            previous=item[8],
            unit=item[9],
        )
        for item in historical_records
    ]

    save_economic_events(events, db_path=db_path)
    return len(events)


if __name__ == "__main__":
    count = seed_historical_macro_data()
    print(f"Successfully seeded {count} historical macro records into fedwatch.db.")
