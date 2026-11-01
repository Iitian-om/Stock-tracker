"""Price sources. PRICE_SOURCE=mock (default, works offline) or yahoo (real prices)."""
import os
import random

import requests

SOURCE = os.getenv("PRICE_SOURCE", "mock").lower()
_last: dict[str, float] = {}


def _mock(symbol: str) -> float:
    base = _last.get(symbol) or random.uniform(100, 3000)
    new = max(1.0, base * (1 + random.gauss(0, 0.003)))
    _last[symbol] = new
    return round(new, 2)


def _yahoo(symbol: str) -> float:
    resp = requests.get(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
        params={"interval": "1m", "range": "1d"},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=10,
    )
    resp.raise_for_status()
    return float(resp.json()["chart"]["result"][0]["meta"]["regularMarketPrice"])


def fetch_price(symbol: str) -> float:
    return _yahoo(symbol) if SOURCE == "yahoo" else _mock(symbol)
