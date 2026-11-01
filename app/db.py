"""Database setup. Uses SQLite locally and PostgreSQL (RDS) on AWS, chosen by DATABASE_URL."""
import os
import time
from datetime import datetime, timezone

from sqlalchemy import (Boolean, Column, DateTime, Float, Index, Integer,
                        String, create_engine)
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/stocks.db")
IS_SQLITE = DATABASE_URL.startswith("sqlite")

if IS_SQLITE:
    os.makedirs("data", exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if IS_SQLITE else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Price(Base):
    __tablename__ = "prices"
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    price = Column(Float, nullable=False)
    ts = Column(DateTime, nullable=False, default=utcnow)
    __table_args__ = (Index("ix_prices_symbol_ts", "symbol", "ts"),)


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    condition = Column(String(5), nullable=False)  # "above" or "below"
    threshold = Column(Float, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)
    triggered_at = Column(DateTime, nullable=True)
    triggered_price = Column(Float, nullable=True)


def init_db(retries: int = 10, delay: float = 3.0) -> None:
    """Create tables. Retries so containers survive the DB starting late."""
    for attempt in range(1, retries + 1):
        try:
            Base.metadata.create_all(engine)
            return
        except Exception as exc:  # noqa: BLE001
            print(f"[db] init attempt {attempt}/{retries} failed: {exc}", flush=True)
            time.sleep(delay)
    raise RuntimeError("Database not reachable")
