from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd


def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def rsi(s: pd.Series, n: int = 14) -> pd.Series:
    d = s.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = up / dn.replace(0, float("nan"))
    return (100 - (100 / (1 + rs))).fillna(50.0)


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    prev = df.close.shift(1)
    tr = pd.concat([(df.high - df.low), (df.high - prev).abs(), (df.low - prev).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    for c in ("open", "high", "low", "close", "volume"):
        x[c] = pd.to_numeric(x[c], errors="coerce")
    return x.dropna(subset=["high", "low", "close", "volume"])


def _trend(df: pd.DataFrame) -> int:
    x = _clean(df)
    if len(x) < 55: return 0
    e20 = ema(x.close, 20)
    e50 = ema(x.close, 50)
    slope = e20.iloc[-1] - e20.iloc[-6]
    if e20.iloc[-1] > e50.iloc[-1] and slope > 0: return 1
    if e20.iloc[-1] < e50.iloc[-1] and slope < 0: return -1
    return 0


def _structure(df: pd.DataFrame, n: int = 9) -> dict[str, Any]:
    x = _clean(df)
    if len(x) < n * 3: return {"bos": 0, "choch": 0, "swing_high": float(x.high.iloc[-1]), "swing_low": float(x.low.iloc[-1])}
    hi, lo, last = x.high.iloc[-n-1:-1].max(), x.low.iloc[-n-1:-1].min(), x.iloc[-1]
    bos = 1 if last.close > hi else -1 if last.close < lo else 0
    prev = x.close.iloc[-2]
    choch = 1 if bos == 1 and prev <= hi else -1 if bos == -1 and prev >= lo else 0
    return {"bos": bos, "choch": choch, "swing_high": float(hi), "swing_low": float(lo)}


def _sweep(df: pd.DataFrame, n: int = 12) -> dict[str, bool]:
    x = _clean(df)
    if len(x) < n + 2: return {"high": False, "low": False}
    prior_hi, prior_lo, c = x.high.iloc[-n-1:-1].max(), x.low.iloc[-n-1:-1].min(), x.iloc[-1]
    return {"high": bool(c.high > prior_hi and c.close < prior_hi), "low": bool(c.low < prior_lo and c.close > prior_lo)}


def _fvg(df: pd.DataFrame) -> dict[str, bool]:
    x = _clean(df)
    if len(x) < 3: return {"bull": False, "bear": False}
    a, _, c = x.iloc[-3], x.iloc[-2], x.iloc[-1]
    return {"bull": bool(c.low > a.high), "bear": bool(c.high < a.low)}


def _volume_ratio(df: pd.DataFrame, n: int = 20) -> float:
    x = _clean(df)
    if len(x) < n + 1: return 1.0
    base = x.volume.iloc[-n-1:-1].mean()
    return float(x.volume.iloc[-1] / base) if base else 1.0


@dataclass
class Setup:
    symbol: str; direction: str; score: float; confidence: float; price: float; trigger: float; stop: float; tp1: float; tp2: float; rr: float; reasons: list[str]; warnings: list[str]; features: dict[str, Any]
    def to_dict(self) -> dict[str, Any]: return asdict(self)


def analyze(symbol: str, frames: dict[str, pd.DataFrame], tv: dict[str, Any] | None = None, min_score: float = 45) -> list[dict[str, Any]]:
    required = ("4h", "1h", "15m")
    if any(k not in frames or frames[k] is None or len(frames[k]) < 60 for k in required): return []
    d4, d1, d15 = (_clean(frames[k]) for k in required)
    price, a15 = float(d15.close.iloc[-1]), float(atr(d15).iloc[-1])
    if not a15 or a15 <= 0: return []
    t4, t1, s1, s15, sw15, fv15, vr, r = _trend(d4), _trend(d1), _structure(d1), _structure(d15), _sweep(d15), _fvg(d15), _volume_ratio(d15), float(rsi(d15.close).iloc[-1])
    results = []
    for direction, sign in (("LONG", 1), ("SHORT", -1)):
        score, reasons, warnings = 0.0, [], []
        if t4 == sign: score += 20; reasons.append("4H trend aligned")
        elif t4 == -sign: score -= 15; warnings.append("4H trend against setup")
        if t1 == sign: score += 15; reasons.append("1H trend aligned")
        if s1["bos"] == sign: score += 10; reasons.append("1H BOS")
        if s15["bos"] == sign: score += 10; reasons.append("15M BOS")
        if (sw15["low"] if sign == 1 else sw15["high"]): score += 10; reasons.append("liquidity sweep")
        if (fv15["bull"] if sign == 1 else fv15["bear"]): score += 8; reasons.append("15M FVG")
        if vr >= 1.5: score += 15; reasons.append(f"volume expansion {vr:.1f}x")
        elif vr >= 1.2: score += 8; reasons.append(f"volume expansion {vr:.1f}x")
        if (r >= 50 if sign == 1 else r <= 50): score += 5; reasons.append("RSI supports direction")
        if tv:
            try:
                tvv = float(tv.get("15m", {}).get("Recommend.All"))
                if (tvv > 0 if sign == 1 else tvv < 0): score += 5; reasons.append("TradingView confirmation")
                else: warnings.append("TradingView not aligned")
            except (TypeError, ValueError): pass
        trigger = float(s15["swing_high"] if sign == 1 else s15["swing_low"]); distance = abs(trigger - price)
        if distance > a15: warnings.append("trigger farther than 1 ATR"); score -= 10
        risk = max(a15 * 1.2, distance * 0.75); stop = price - risk if sign == 1 else price + risk; tp1 = price + risk * 2 * sign; tp2 = price + risk * 3 * sign
        score = max(0.0, min(100.0, score)); confidence = min(95.0, max(0.0, score * 0.9 + (5 if t4 == sign and t1 == sign else 0)))
        if score >= min_score:
            results.append(Setup(symbol, direction, round(score, 2), round(confidence, 2), price, trigger, stop, tp1, tp2, 2.0, reasons, warnings, {"trend_4h": t4, "trend_1h": t1, "rsi_15m": round(r, 2), "atr_15m": a15, "volume_ratio": round(vr, 2), "bos_1h": s1["bos"], "bos_15m": s15["bos"], "sweep": sw15, "fvg": fv15}).to_dict())
    return sorted(results, key=lambda x: (x["score"], x["confidence"]), reverse=True)
