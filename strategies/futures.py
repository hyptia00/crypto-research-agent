# ============================================================
# FUTURES STRATEGY ENGINE
# ============================================================

from typing import Any, Dict, Optional

from market.indicators import calculate_indicators
from market.structure import analyze_structure


def _float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _get(df, name, default=0.0):
    if df is None or len(df) == 0:
        return default

    if name not in df.columns:
        return default

    return _float(df[name].iloc[-1], default)


def _build_levels(
    price: float,
    atr: float,
    direction: str,
):
    """
    ATR tabanlı başlangıç stop/TP seviyeleri.
    """

    if atr <= 0:
        atr = price * 0.01

    if direction == "LONG":

        stop = price - (atr * 1.5)
        tp1 = price + (atr * 2.0)
        tp2 = price + (atr * 3.0)

    else:

        stop = price + (atr * 1.5)
        tp1 = price - (atr * 2.0)
        tp2 = price - (atr * 3.0)

    return stop, tp1, tp2


def analyze_futures(
    df,
    symbol: str,
    btc_regime: Optional[str] = None,
) -> Dict[str, Any]:

    symbol = symbol.upper()

    if df is None or len(df) < 50:

        return {
            "symbol": symbol,
            "direction": "WAIT",
            "strategy": "FUTURES",
            "score": 0,
            "confidence": 0,
            "reason": "INSUFFICIENT_DATA",
        }

    # --------------------------------------------------------
    # INDICATORS
    # --------------------------------------------------------

    try:
        data = calculate_indicators(df)
    except Exception:

        data = df.copy()

    # --------------------------------------------------------
    # STRUCTURE
    # --------------------------------------------------------

    try:
        structure = analyze_structure(data)
    except Exception:

        structure = {
            "trend": "UNKNOWN",
            "structure": "UNKNOWN",
            "bos": False,
            "choch": False,
        }

    price = _get(data, "close")

    ema20 = _get(
        data,
        "ema20",
        _get(data, "EMA20")
    )

    ema50 = _get(
        data,
        "ema50",
        _get(data, "EMA50")
    )

    rsi = _get(
        data,
        "rsi",
        _get(data, "RSI")
    )

    macd = _get(
        data,
        "macd",
        _get(data, "MACD")
    )

    atr = _get(
        data,
        "atr",
        _get(data, "ATR")
    )

    volume = _get(data, "volume")

    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    long_score = 0
    short_score = 0

    reasons_long = []
    reasons_short = []

    # --------------------------------------------------------
    # TREND
    # --------------------------------------------------------

    trend = str(
        structure.get(
            "trend",
            "UNKNOWN"
        )
    ).upper()

    if trend in ("UP", "LONG", "BULLISH"):

        long_score += 2

        reasons_long.append(
            "market structure bullish"
        )

    elif trend in ("DOWN", "SHORT", "BEARISH"):

        short_score += 2

        reasons_short.append(
            "market structure bearish"
        )

    # --------------------------------------------------------
    # EMA
    # --------------------------------------------------------

    if price > ema20 > ema50:

        long_score += 2

        reasons_long.append(
            "price above EMA20/EMA50"
        )

    elif price < ema20 < ema50:

        short_score += 2

        reasons_short.append(
            "price below EMA20/EMA50"
        )

    # --------------------------------------------------------
    # RSI
    # --------------------------------------------------------

    if 50 <= rsi <= 68:

        long_score += 1

        reasons_long.append(
            f"RSI bullish zone ({rsi:.1f})"
        )

    elif 32 <= rsi <= 50:

        short_score += 1

        reasons_short.append(
            f"RSI bearish zone ({rsi:.1f})"
        )

    # --------------------------------------------------------
    # MACD
    # --------------------------------------------------------

    if macd > 0:

        long_score += 1

        reasons_long.append(
            "MACD positive"
        )

    elif macd < 0:

        short_score += 1

        reasons_short.append(
            "MACD negative"
        )

    # --------------------------------------------------------
    # BREAK OF STRUCTURE
    # --------------------------------------------------------

    if structure.get("bos"):

        if trend in ("UP", "LONG", "BULLISH"):

            long_score += 1

            reasons_long.append(
                "bullish BOS"
            )

        elif trend in (
            "DOWN",
            "SHORT",
            "BEARISH"
        ):

            short_score += 1

            reasons_short.append(
                "bearish BOS"
            )

    # --------------------------------------------------------
    # BTC REGIME
    # --------------------------------------------------------

    regime = str(
        btc_regime or "UNKNOWN"
    ).upper()

    if regime == "LONG":

        long_score += 1

        if short_score > 0:
            short_score -= 1

    elif regime == "SHORT":

        short_score += 1

        if long_score > 0:
            long_score -= 1

    # --------------------------------------------------------
    # DIRECTION
    # --------------------------------------------------------

    if long_score > short_score:

        direction = "LONG"
        score = long_score
        reasons = reasons_long

    elif short_score > long_score:

        direction = "SHORT"
        score = short_score
        reasons = reasons_short

    else:

        return {
            "symbol": symbol,
            "direction": "WAIT",
            "strategy": "FUTURES",
            "score": 0,
            "confidence": 0,
            "reason":
                "LONG_SHORT_CONFLICT",
        }

    # --------------------------------------------------------
    # MINIMUM SCORE
    # --------------------------------------------------------

    if score < 4:

        return {
            "symbol": symbol,
            "direction": "WAIT",
            "strategy": "FUTURES",
            "score": score,
            "confidence": 0,
            "reason":
                "INSUFFICIENT_CONFIRMATION",
            "details": reasons,
        }

    # --------------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------------

    confidence = min(
        95,
        50 + (score * 7)
    )

    # BTC ters yöndeyse confidence azalt
    if (
        regime == "LONG"
        and direction == "SHORT"
    ):

        confidence -= 15

    if (
        regime == "SHORT"
        and direction == "LONG"
    ):

        confidence -= 15

    confidence = max(
        0,
        min(100, confidence)
    )

    # --------------------------------------------------------
    # LEVELS
    # --------------------------------------------------------

    stop, tp1, tp2 = _build_levels(
        price,
        atr,
        direction,
    )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    return {
        "symbol": symbol,
        "direction": direction,
        "action": direction,
        "strategy": "FUTURES",

        "score": score,
        "confidence": round(
            confidence,
            1
        ),

        "entry": price,
        "price": price,

        "stop": stop,
        "tp1": tp1,
        "tp2": tp2,

        "btc_regime": regime,

        "trend": trend,
        "rsi": rsi,
        "macd": macd,
        "atr": atr,

        "volume": volume,

        "bos": bool(
            structure.get("bos", False)
        ),

        "choch": bool(
            structure.get("choch", False)
        ),

        "reason": reasons,

        "execution_mode": "PAPER",
    }


def scan_futures(
    market_data: Dict[str, Any],
    btc_regime: Optional[str] = None,
):

    results = []

    for symbol, df in (
        market_data or {}
    ).items():

        try:

            result = analyze_futures(
                df=df,
                symbol=symbol,
                btc_regime=btc_regime,
            )

            results.append(result)

        except Exception as exc:

            results.append({
                "symbol": symbol,
                "direction": "WAIT",
                "strategy": "FUTURES",
                "score": 0,
                "confidence": 0,
                "reason":
                    f"ANALYSIS_ERROR: {exc}",
            })

    return results
