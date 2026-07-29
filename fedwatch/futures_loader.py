from __future__ import annotations

from datetime import date

import yfinance as yf

_MONTH_CODES = {
    1: "F", 2: "G", 3: "H", 4: "J", 5: "K", 6: "M",
    7: "N", 8: "Q", 9: "U", 10: "V", 11: "X", 12: "Z",
}


def fed_funds_ticker(year: int, month: int) -> str:
    code = _MONTH_CODES[month]
    yy = year % 100
    return f"ZQ{code}{yy:02d}.CBT"


def get_futures_price(year: int, month: int) -> float:
    ticker = fed_funds_ticker(year, month)
    hist = yf.Ticker(ticker).history(period="5d")
    if hist.empty:
        raise ValueError(f"No data for {ticker} — contract may not be actively quoted on Yahoo Finance")
    return float(hist["Close"].iloc[-1])


def get_futures_price_for_meeting(decision_date: date) -> float:
    return get_futures_price(decision_date.year, decision_date.month)
