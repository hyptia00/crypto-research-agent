from __future__ import annotations

import pandas as pd


def candles_to_df(raw: list[list]) -> pd.DataFrame:
    if not raw:
        return pd.DataFrame()
    # Binance: 12 fields; Bybit/OKX: timestamp, o,h,l,c,vol,...
    rows = []
    for r in raw:
        try:
            rows.append({"time": pd.to_datetime(int(r[0]), unit="ms", utc=True), "open": float(r[1]), "high": float(r[2]), "low": float(r[3]), "close": float(r[4]), "volume": float(r[5])})
        except (IndexError, TypeError, ValueError):
            continue
    return pd.DataFrame(rows).set_index("time") if rows else pd.DataFrame()


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    if len(x) < 30:
        return x
    delta = x.close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
    rs = gain / loss.replace(0, pd.NA)
    x["rsi"] = (100 - (100 / (1 + rs))).astype(float)
    x["ema20"] = x.close.ewm(span=20, adjust=False).mean()
    x["ema50"] = x.close.ewm(span=50, adjust=False).mean()
    prev = x.close.shift(1)
    tr = pd.concat([(x.high - x.low), (x.high - prev).abs(), (x.low - prev).abs()], axis=1).max(axis=1)
    x["atr"] = tr.rolling(14).mean()
    x["vol_ma20"] = x.volume.rolling(20).mean()
    x["range_high"] = x.high.rolling(20).max().shift(1)
    x["range_low"] = x.low.rolling(20).min().shift(1)
    return x


def structure(df: pd.DataFrame) -> dict:
    if len(df) < 30:
        return {"trend": "unknown", "bos_up": False, "bos_down": False, "sweep_high": False, "sweep_low": False}
    x = enrich(df)
    last = x.iloc[-1]
    prev = x.iloc[-2]
    trend = "bullish" if last.ema20 > last.ema50 else "bearish"
    bos_up = bool(last.close > last.range_high) if pd.notna(last.range_high) else False
    bos_down = bool(last.close < last.range_low) if pd.notna(last.range_low) else False
    sweep_high = bool(last.high > prev.range_high and last.close < prev.range_high) if pd.notna(prev.range_high) else False
    sweep_low = bool(last.low < prev.range_low and last.close > prev.range_low) if pd.notna(prev.range_low) else False
    return {"trend": trend, "bos_up": bos_up, "bos_down": bos_down, "sweep_high": sweep_high, "sweep_low": sweep_low, "rsi": float(last.rsi) if pd.notna(last.rsi) else None, "atr": float(last.atr) if pd.notna(last.atr) else None, "volume_ratio": float(last.volume / last.vol_ma20) if last.vol_ma20 and pd.notna(last.vol_ma20) else 0.0, "high": float(last.high), "low": float(last.low), "close": float(last.close), "range_high": float(last.range_high) if pd.notna(last.range_high) else None, "range_low": float(last.range_low) if pd.notna(last.range_low) else None}
