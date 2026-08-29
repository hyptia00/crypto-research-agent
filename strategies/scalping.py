# ============================================================
# SCALPING STRATEGY ENGINE
# 15M -> 5M -> 1M
# ============================================================

from typing import Any, Dict, Optional

from market.indicators import calculate_indicators
from market.structure import analyze_structure


def _float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _indicator(df, names, default=0.0):

    if df is None or len(df) == 0:
        return default

    for name in names:

        if name in df.columns:

            return _float(
                df[name].iloc[-1],
                default
            )

    return default


def _trend(df):

    if df is None or len(df) < 20:
        return "UNKNOWN"

    try:
        data = calculate_indicators(df)
    except Exception:
        data = df

    price = _indicator(
        data,
        ["close"]
    )

    ema20 = _indicator(
        data,
        ["ema20", "EMA20"]
    )

    ema50 = _indicator(
        data,
        ["ema50", "EMA50"]
    )

    if price > ema20 > ema50:
        return "BULLISH"

    if price < ema20 < ema50:
        return "BEARISH"

    return "SIDEWAYS"


def _structure(df):

    if df is None or len(df) < 20:
        return {}

    try:
        data = calculate_indicators(df)
        return analyze_structure(data)
    except Exception:
        return {}


def _structure_direction(
    structure
):

    trend = str(
        structure.get(
            "trend",
            ""
        )
    ).upper()

    if trend in (
        "UP",
        "BULLISH",
        "LONG",
    ):
        return "LONG"

    if trend in (
        "DOWN",
        "BEARISH",
        "SHORT",
    ):
        return "SHORT"

    return "UNKNOWN"


def _has_bullish_trigger(
    structure
):

    return (
        structure.get("bos") is True
        or structure.get("choch") is True
    )


def _has_bearish_trigger(
    structure
):

    return (
        structure.get("bos") is True
        or structure.get("choch") is True
    )


def _levels(
    price,
    atr,
    direction,
):

    if atr <= 0:
        atr = price * 0.002

    if direction == "LONG":

        stop = price - (
            atr * 1.2
        )

        tp1 = price + (
            atr * 1.8
        )

        tp2 = price + (
            atr * 2.5
        )

    else:

        stop = price + (
            atr * 1.2
        )

        tp1 = price - (
            atr * 1.8
        )

        tp2 = price - (
            atr * 2.5
        )

    return stop, tp1, tp2


def analyze_scalping(
    data: Dict[str, Any],
    symbol: str,
    btc_regime: Optional[str] = None,
):

    symbol = symbol.upper()

    df15 = data.get("15m")
    df5 = data.get("5m")
    df1 = data.get("1m")

    if (
        df15 is None
        or df5 is None
        or df1 is None
    ):

        return {
            "symbol": symbol,
            "direction": "WAIT",
            "strategy": "SCALPING",
            "score": 0,
            "confidence": 0,
            "reason":
                "MISSING_TIMEFRAMES",
        }

    if (
        len(df15) < 50
        or len(df5) < 50
        or len(df1) < 50
    ):

        return {
            "symbol": symbol,
            "direction": "WAIT",
            "strategy": "SCALPING",
            "score": 0,
            "confidence": 0,
            "reason":
                "INSUFFICIENT_DATA",
        }

    # ========================================================
    # 15M — DIRECTION
    # ========================================================

    trend15 = _trend(df15)

    structure15 = _structure(df15)

    direction15 = _structure_direction(
        structure15
    )

    if trend15 == "BULLISH":

        direction = "LONG"

    elif trend15 == "BEARISH":

        direction = "SHORT"

    else:

        return {
            "symbol": symbol,
            "direction": "WAIT",
            "strategy": "SCALPING",
            "score": 0,
            "confidence": 0,
            "reason":
                "15M_SIDEWAYS",
        }

    # 15M structure ters ise işlem yok.
    if (
        direction15 != "UNKNOWN"
        and direction15 != direction
    ):

        return {
            "symbol": symbol,
            "direction": "WAIT",
            "strategy": "SCALPING",
            "score": 0,
            "confidence": 0,
            "reason":
                "15M_STRUCTURE_CONFLICT",
        }

    score = 0
    reasons = []

    score += 2

    reasons.append(
        f"15M direction = {direction}"
    )

    # --------------------------------------------------------
    # 15M BOS / CHOCH
    # --------------------------------------------------------

    if structure15.get("bos"):

        score += 2

        reasons.append(
            "15M BOS"
        )

    if structure15.get("choch"):

        score += 2

        reasons.append(
            "15M CHoCH"
        )

    # ========================================================
    # 5M — SETUP
    # ========================================================

    trend5 = _trend(df5)

    structure5 = _structure(df5)

    direction5 = _structure_direction(
        structure5
    )

    if direction == "LONG":

        if trend5 != "BULLISH":

            return {
                "symbol": symbol,
                "direction": "WAIT",
                "strategy": "SCALPING",
                "score": score,
                "confidence": 0,
                "reason":
                    "5M_NOT_ALIGNED",
            }

    else:

        if trend5 != "BEARISH":

            return {
                "symbol": symbol,
                "direction": "WAIT",
                "strategy": "SCALPING",
                "score": score,
                "confidence": 0,
                "reason":
                    "5M_NOT_ALIGNED",
            }

    score += 2

    reasons.append(
        "5M trend aligned"
    )

    if (
        direction5 != "UNKNOWN"
        and direction5 == direction
    ):

        score += 2

        reasons.append(
            "5M structure aligned"
        )

    # --------------------------------------------------------
    # 5M STRUCTURE EVENT
    # --------------------------------------------------------

    if structure5.get("bos"):

        score += 2

        reasons.append(
            "5M BOS setup"
        )

    if structure5.get("choch"):

        score += 2

        reasons.append(
            "5M CHoCH setup"
        )

    # ========================================================
    # 1M
