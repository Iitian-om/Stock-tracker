"""REST API for the Stock Price Tracker & Alert service."""
import os
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from .db import Alert, Price, SessionLocal, init_db, utcnow

INTERVAL = int(os.getenv("FETCH_INTERVAL", "60"))
STATIC = Path(__file__).parent / "static"

app = FastAPI(title="Stock Price Tracker & Alert API", version="1.0")


@app.on_event("startup")
def _startup() -> None:
    init_db()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class AlertIn(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    condition: Literal["above", "below"]
    threshold: float = Field(gt=0)


def _price_dict(p: Price) -> dict:
    return {"symbol": p.symbol, "price": p.price, "ts": p.ts.isoformat() + "Z"}


def _alert_dict(a: Alert) -> dict:
    return {
        "id": a.id, "symbol": a.symbol, "condition": a.condition, "threshold": a.threshold,
        "active": a.active,
        "triggered_at": a.triggered_at.isoformat() + "Z" if a.triggered_at else None,
        "triggered_price": a.triggered_price,
    }


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(STATIC / "index.html")


@app.get("/health")
def health(db: Session = Depends(get_db)):
    """Used by Docker/CloudWatch. 503 if DB is down; reports data freshness for the SLA."""
    try:
        db.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=503, detail={"status": "down", "db": "unreachable"})
    latest = db.query(Price).order_by(Price.ts.desc()).first()
    age = int((utcnow() - latest.ts).total_seconds()) if latest else None
    worker = "ok" if age is not None and age <= INTERVAL * 3 else "stale"
    return {"status": "ok", "db": "ok", "worker": worker, "data_age_seconds": age}


@app.get("/prices")
def latest_prices(db: Session = Depends(get_db)):
    symbols = [r[0] for r in db.query(Price.symbol).distinct().all()]
    out = []
    for s in sorted(symbols):
        p = db.query(Price).filter(Price.symbol == s).order_by(Price.ts.desc()).first()
        out.append(_price_dict(p))
    return out


@app.get("/price/{symbol}")
def price(symbol: str, db: Session = Depends(get_db)):
    p = db.query(Price).filter(Price.symbol == symbol.upper()).order_by(Price.ts.desc()).first()
    if not p:
        raise HTTPException(404, f"No data for {symbol.upper()}")
    return _price_dict(p)


@app.get("/history/{symbol}")
def history(symbol: str, limit: int = 100, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 1000))
    rows = (db.query(Price).filter(Price.symbol == symbol.upper())
            .order_by(Price.ts.desc()).limit(limit).all())
    return [_price_dict(r) for r in reversed(rows)]


@app.post("/alerts", status_code=201)
def create_alert(body: AlertIn, db: Session = Depends(get_db)):
    a = Alert(symbol=body.symbol.upper(), condition=body.condition, threshold=body.threshold)
    db.add(a)
    db.commit()
    db.refresh(a)
    return _alert_dict(a)


@app.get("/alerts")
def list_alerts(db: Session = Depends(get_db)):
    return [_alert_dict(a) for a in db.query(Alert).order_by(Alert.id.desc()).all()]


@app.delete("/alerts/{alert_id}")
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    a = db.get(Alert, alert_id)
    if not a:
        raise HTTPException(404, "Alert not found")
    db.delete(a)
    db.commit()
    return {"deleted": alert_id}
