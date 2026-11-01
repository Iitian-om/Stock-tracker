"""Background worker: fetch prices on an interval, store them, evaluate alerts."""
import os
import time

from .db import Alert, Price, SessionLocal, init_db, utcnow
from .sources import fetch_price

SYMBOLS = [s.strip().upper() for s in os.getenv("SYMBOLS", "RELIANCE.NS,TCS.NS,INFY.NS,AAPL").split(",") if s.strip()]
INTERVAL = int(os.getenv("FETCH_INTERVAL", "60"))


def check_alerts(db, symbol: str, price: float) -> None:
    alerts = db.query(Alert).filter(Alert.symbol == symbol, Alert.active.is_(True)).all()
    for a in alerts:
        hit = (a.condition == "above" and price >= a.threshold) or (
            a.condition == "below" and price <= a.threshold
        )
        if hit:
            a.active = False
            a.triggered_at = utcnow()
            a.triggered_price = price
            print(f"[alert] #{a.id} {symbol} {a.condition} {a.threshold} triggered at {price}", flush=True)


def run_once() -> None:
    db = SessionLocal()
    try:
        for symbol in SYMBOLS:
            try:
                price = fetch_price(symbol)
            except Exception as exc:  # noqa: BLE001
                print(f"[worker] fetch failed for {symbol}: {exc}", flush=True)
                continue
            db.add(Price(symbol=symbol, price=price, ts=utcnow()))
            check_alerts(db, symbol, price)
        db.commit()
        print(f"[worker] stored prices for {len(SYMBOLS)} symbols", flush=True)
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        print(f"[worker] cycle failed: {exc}", flush=True)
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    print(f"[worker] started; symbols={SYMBOLS} interval={INTERVAL}s", flush=True)
    while True:
        run_once()
        time.sleep(INTERVAL)
