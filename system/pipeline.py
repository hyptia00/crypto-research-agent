from __future__ import annotations

import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any

from .alerts import detect_alerts
from .analysis import analyze_symbol
from .config import Settings
from .cryptometer import CryptoMeterClient, CryptoMeterConfig
from .event_intel import EventIntel
from .exchanges import depth_imbalance, make_exchange, trade_delta
from .storage import Store
from .technical import candles_to_df


class TradingIntelligence:
    """Analysis-only pipeline. There is intentionally no order/execution client."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.from_env()
        self.store = Store(self.settings.database_path)
        self.events = EventIntel(self.settings.agent_reach_enabled, self.settings.event_timeout_seconds)
        self.clients = {name: make_exchange(name) for name in self.settings.exchanges}
        self.cvd_history: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=50))
        self.cryptometer = CryptoMeterClient(
            CryptoMeterConfig(
                api_key=self.settings.cryptometer_api_key if self.settings.cryptometer_enabled else "",
                timeout_seconds=self.settings.cryptometer_timeout_seconds,
                cache_seconds=self.settings.cryptometer_cache_seconds,
            )
        )

    def _exchange_snapshot(self, name: str, symbol: str) -> dict[str, Any] | None:
        client = self.clients[name]
        try:
            raw = client.snapshot(symbol, self.settings.cvd_trade_limit, self.settings.orderbook_limit)
            prev = self.store.previous_snapshot(name, symbol)
            previous_oi = float(prev["oi"]) if prev and prev.get("oi") else None
            oi = float(raw["oi"])
            oi_change = ((oi - previous_oi) / previous_oi * 100.0) if previous_oi else 0.0
            delta = trade_delta(name, raw.get("trades", []))
            previous_cvd = float(prev.get("cvd", 0.0)) if prev else 0.0
            cvd = previous_cvd + delta
            bid, ask, imbalance = depth_imbalance(raw["depth"])
            liquidation = 0.0
            for item in raw.get("liquidations", []):
                try:
                    if name == "binance":
                        liquidation += float(item.get("origQty", 0)) * float(item.get("price", 0))
                except (TypeError, ValueError):
                    pass
            payload = {"price": raw["price"], "oi": oi, "funding": raw["funding"], "cvd": cvd, "cvd_delta": delta, "oi_change_pct": oi_change, "orderbook_imbalance": imbalance, "bid_depth": bid, "ask_depth": ask, "liquidations": liquidation}
            ts = datetime.now(timezone.utc).isoformat()
            self.store.add_snapshot(ts, name, symbol, payload)
            return payload
        except Exception as exc:
            return {"exchange": name, "error": str(exc)}

    def scan_symbol(self, symbol: str) -> dict[str, Any]:
        symbol = symbol.upper()
        market_rows = {name: self._exchange_snapshot(name, symbol) for name in self.clients}
        good = {k: v for k, v in market_rows.items() if v and "error" not in v}
        if not good:
            return {"symbol": symbol, "status": "DATA_UNAVAILABLE", "exchanges": market_rows}

        primary = good.get("binance") or next(iter(good.values()))
        cvd_delta = sum(float(v.get("cvd_delta", 0)) for v in good.values())
        cvd_hist = self.cvd_history[symbol]
        cvd_hist.append(cvd_delta)
        mean = sum(cvd_hist) / len(cvd_hist)
        std = (sum((x - mean) ** 2 for x in cvd_hist) / max(1, len(cvd_hist) - 1)) ** 0.5
        cvd_z = (cvd_delta - mean) / std if std else 0.0
        market = {
            "price": sum(float(v["price"]) for v in good.values()) / len(good),
            "oi": sum(float(v["oi"]) for v in good.values()) / len(good),
            "oi_change_pct": sum(float(v["oi_change_pct"]) for v in good.values()) / len(good),
            "funding": sum(float(v["funding"]) for v in good.values()) / len(good),
            "cvd_delta": cvd_delta,
            "cvd_delta_z": cvd_z,
            "orderbook_imbalance": sum(float(v["orderbook_imbalance"]) for v in good.values()) / len(good),
            "liquidations": sum(float(v.get("liquidations", 0)) for v in good.values()),
            "exchange_count": len(good),
        }

        frames = {}
        try:
            for tf in ("4h", "1h", "15m", "5m", "1m"):
                frames[tf] = candles_to_df(self.clients["binance"].candles(symbol, tf, self.settings.candle_limit))
        except Exception as exc:
            return {"symbol": symbol, "status": "PARTIAL_DATA", "market": market, "error": str(exc), "exchanges": market_rows}

        events = self.events.collect(symbol, self.settings.event_limit)
        cryptometer = self.cryptometer.signal(symbol)
        market["cryptometer"] = cryptometer
        result = analyze_symbol(symbol, frames, market, events)
        alerts = detect_alerts(symbol, market, result.to_dict(), self.settings.alert_threshold)
        data = result.to_dict()
        data["alerts"] = [a.__dict__ for a in alerts]
        data["exchanges"] = market_rows
        self.store.add_analysis(result.timestamp.isoformat(), symbol, data)
        return data

    def scan_once(self) -> list[dict[str, Any]]:
        return [self.scan_symbol(symbol) for symbol in self.settings.symbols]

    def run_forever(self) -> None:
        while True:
            started = time.monotonic()
            try:
                for result in self.scan_once():
                    print(result)
            except Exception as exc:
                print(f"PIPELINE ERROR: {exc}")
            time.sleep(max(0.0, self.settings.scan_interval_seconds - (time.monotonic() - started)))
