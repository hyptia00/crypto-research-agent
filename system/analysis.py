from __future__ import annotations

from datetime import datetime, timezone
from statistics import mean
from typing import Any

from .models import AnalysisResult, Event
from .technical import structure


def _event_dict(event: Event) -> dict[str, Any]:
    return {"source": event.source, "title": event.title, "url": event.url, "published_at": event.published_at.isoformat() if event.published_at else None, "text": event.text, "relevance": event.relevance, "sentiment": event.sentiment, "tags": event.tags}


def analyze_symbol(symbol: str, frames: dict[str, Any], market: dict[str, Any], events: list[Event]) -> AnalysisResult:
    s4 = structure(frames.get("4h")); s1 = structure(frames.get("1h")); s15 = structure(frames.get("15m")); s5 = structure(frames.get("5m"))
    price = float(market["price"])
    score = 50.0
    reasons: list[str] = []
    bull = sum(x.get("trend") == "bullish" for x in (s4, s1, s15))
    bear = sum(x.get("trend") == "bearish" for x in (s4, s1, s15))
    if bull > bear: score += 8; reasons.append("HTF trend alignment bullish")
    elif bear > bull: score -= 8; reasons.append("HTF trend alignment bearish")
    if s15.get("bos_up"): score += 12; reasons.append("15m bullish BOS")
    if s15.get("bos_down"): score -= 12; reasons.append("15m bearish BOS")
    if s5.get("bos_up"): score += 8; reasons.append("5m bullish breakout structure")
    if s5.get("bos_down"): score -= 8; reasons.append("5m bearish breakout structure")
    if s15.get("sweep_low"): score += 6; reasons.append("15m sell-side liquidity sweep")
    if s15.get("sweep_high"): score -= 6; reasons.append("15m buy-side liquidity sweep")
    vr = s15.get("volume_ratio", 0.0)
    if vr >= 1.5:
        if s15.get("close", price) >= (s15.get("range_high") or price): score += 7
        if s15.get("close", price) <= (s15.get("range_low") or price): score -= 7
        reasons.append(f"15m volume expansion {vr:.2f}x")
    oi_change = float(market.get("oi_change_pct", 0.0)); cvd_delta = float(market.get("cvd_delta", 0.0)); ob = float(market.get("orderbook_imbalance", 0.0))
    if oi_change > 1.0 and cvd_delta > 0: score += 8; reasons.append("OI expansion + positive CVD")
    elif oi_change > 1.0 and cvd_delta < 0: score -= 6; reasons.append("OI expansion + negative CVD")
    elif oi_change < -1.0: reasons.append("OI contraction / deleveraging")
    if ob > 0.15: score += 4; reasons.append("orderbook bid imbalance")
    elif ob < -0.15: score -= 4; reasons.append("orderbook ask imbalance")
    cm = market.get("cryptometer") or {}
    if cm.get("enabled"):
        cm_score = float(cm.get("score", 0.0))
        score += cm_score * 10.0
        if cm_score > 0.2: reasons.append(f"CryptoMeter corroboration bullish ({cm_score:+.2f})")
        elif cm_score < -0.2: reasons.append(f"CryptoMeter corroboration bearish ({cm_score:+.2f})")
        else: reasons.append("CryptoMeter signal neutral/mixed")
    event_sent = mean([e.sentiment for e in events]) if events else 0.0; event_rel = mean([e.relevance for e in events]) if events else 0.0
    score += event_sent * 6 * event_rel
    if events: reasons.append(f"event intelligence: {len(events)} relevant items")
    score = max(0.0, min(100.0, score))
    direction = "LONG" if score >= 60 else "SHORT" if score <= 40 else "NEUTRAL"
    confidence = min(100.0, abs(score - 50.0) * 2)
    status = "WATCH" if 40 < score < 60 else "SETUP"
    atr = s15.get("atr") or max(price * 0.005, 1e-9)
    if direction == "LONG": invalidation, targets = price - atr * 1.5, [price + atr * 2, price + atr * 3]
    elif direction == "SHORT": invalidation, targets = price + atr * 1.5, [price - atr * 2, price - atr * 3]
    else: invalidation, targets = None, []
    return AnalysisResult(symbol, datetime.now(timezone.utc), direction, round(score, 2), round(confidence, 2), status, reasons, invalidation, targets, market, [_event_dict(e) for e in events])
