from __future__ import annotations

import tempfile
from datetime import datetime, timezone

import pandas as pd

from system.alerts import detect_alerts
from system.analysis import analyze_symbol
from system.exchanges import depth_imbalance, trade_delta
from system.models import Event
from system.storage import Store
from system.technical import enrich, structure


def sample_df(n=80):
    idx = pd.date_range("2026-01-01", periods=n, freq="15min", tz="UTC")
    close = [100 + i * 0.2 for i in range(n)]
    return pd.DataFrame({"open": close, "high": [x + 1 for x in close], "low": [x - 1 for x in close], "close": close, "volume": [100] * n}, index=idx)


def test_indicators_and_structure():
    x = enrich(sample_df())
    s = structure(x)
    assert s["trend"] == "bullish"
    assert s["atr"] is not None
    assert s["rsi"] is not None


def test_trade_delta_and_orderbook():
    assert trade_delta("binance", [{"q": "2", "m": False}, {"q": "1", "m": True}]) == 1
    bid, ask, imb = depth_imbalance({"bids": [[100, 2]], "asks": [[100, 1]]})
    assert bid == 200 and ask == 100 and imb > 0


def test_analysis_and_alerts():
    frames = {tf: sample_df() for tf in ("4h", "1h", "15m", "5m", "1m")}
    market = {"price": 116, "oi_change_pct": 2.5, "cvd_delta": 50, "cvd_delta_z": 2.5, "orderbook_imbalance": 0.35, "liquidations": 10000}
    event = Event("test", "BTC ETF approval", "https://example.com", datetime.now(timezone.utc), "BTC ETF approval", 0.9, 0.8, ["BTC", "ETF"])
    result = analyze_symbol("BTCUSDT", frames, market, [event])
    assert 0 <= result.score <= 100
    assert result.to_dict()["events"][0]["published_at"] is not None
    alerts = detect_alerts("BTCUSDT", market, result.to_dict(), 70)
    assert alerts


def test_store_roundtrip():
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        store = Store(f.name)
        store.add_snapshot("2026-01-01T00:00:00+00:00", "binance", "BTCUSDT", {"oi": 10, "cvd": 2})
        assert store.previous_snapshot("binance", "BTCUSDT")["oi"] == 10
