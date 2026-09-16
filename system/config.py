from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    symbols: tuple[str, ...] = ("BTCUSDT", "ETHUSDT")
    exchanges: tuple[str, ...] = ("binance", "bybit", "okx")
    scan_interval_seconds: int = 30
    timeframe: str = "15m"
    candle_limit: int = 250
    min_quote_volume: float = 10_000_000.0
    cvd_trade_limit: int = 1000
    orderbook_limit: int = 50
    event_limit: int = 10
    event_timeout_seconds: int = 12
    database_path: str = "data/lilith.db"
    agent_reach_enabled: bool = True
    alert_threshold: float = 70.0

    @classmethod
    def from_env(cls) -> "Settings":
        symbols = tuple(x.strip().upper() for x in os.getenv("LILITH_SYMBOLS", "BTCUSDT,ETHUSDT").split(",") if x.strip())
        exchanges = tuple(x.strip().lower() for x in os.getenv("LILITH_EXCHANGES", "binance,bybit,okx").split(",") if x.strip())
        return cls(
            symbols=symbols,
            exchanges=exchanges,
            scan_interval_seconds=int(os.getenv("LILITH_INTERVAL", "30")),
            timeframe=os.getenv("LILITH_TIMEFRAME", "15m"),
            candle_limit=int(os.getenv("LILITH_CANDLE_LIMIT", "250")),
            min_quote_volume=float(os.getenv("LILITH_MIN_VOLUME", "10000000")),
            cvd_trade_limit=int(os.getenv("LILITH_CVD_TRADES", "1000")),
            orderbook_limit=int(os.getenv("LILITH_ORDERBOOK_LIMIT", "50")),
            event_limit=int(os.getenv("LILITH_EVENT_LIMIT", "10")),
            event_timeout_seconds=int(os.getenv("LILITH_EVENT_TIMEOUT", "12")),
            database_path=os.getenv("LILITH_DB", "data/lilith.db"),
            agent_reach_enabled=os.getenv("LILITH_AGENT_REACH", "1") not in {"0", "false", "False"},
            alert_threshold=float(os.getenv("LILITH_ALERT_THRESHOLD", "70")),
        )
