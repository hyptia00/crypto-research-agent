# ============================================================
# SPOT STRATEGY ENGINE
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


def _levels(price, atr):

    if atr <= 0:
        atr = price * 0.01

    stop = price - (atr * 1.5)
    tp1 = price + (atr * 2.0)
    tp2 = price + (atr * 3.0)

    return stop, tp1, tp2


def analyze_spot(
    df,
    symbol: str,
    btc_regime: Optional[str] = None,
) -> Dict[str, Any]:

    symbol = symbol.upper()

    if df is None or len(df) < 50:

        return {
            "symbol": symbol,
            "direction": "WAIT",
            "action": "NO_TRADE",
            "strategy": "SPOT",
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
    # MARKET STRUCTURE
    # --------------------------------------------------------

    try:
        structure = analyze_structure(data)
    except Exception:

        structure = {
            "trend": "UNKNOWN",
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

    trend = str(
        structure.get(
            "trend",
            "UNKNOWN"
        )
    ).upper()

    # --------------------------------------------------------
    # SPOT SCORE
    # --------------------------------------------------------

    score = 0
    reasons = []

    # --------------------------------------------------------
    # TREND
    # --------------------------------------------------------

    if trend in (
        "UP",
        "LONG",
        "BULLISH"
    ):

        score += 2

        reasons.append(
            "bullish market structure"
        )

    elif trend in (
        "DOWN",
        "SHORT",
        "BEARISH"
    ):

        score -= 2

        reasons.append(
            "bearish market structure"
        )

    # --------------------------------------------------------
    # EMA
    # --------------------------------------------------------

    if price > ema20 > ema50:

        score += 2

        reasons.append(
            "price above EMA20 and EMA50"
        )

    elif price < ema20 < ema50:

        score -= 2

        reasons.append(
            "price below EMA20 and EMA50"
        )

    # --------------------------------------------------------
    # RSI
    # --------------------------------------------------------

    if 50 <= rsi <= 68:

        score += 1

        reasons.append(
            f"RSI healthy ({rsi:.1f})"
        )

    elif rsi < 30:

        # Aşırı satım tek başına alım sinyali değildir.
        # Sadece olası recovery için küçük katkı.
        score += 1

        reasons.append(
            f"RSI oversold ({rsi:.1f})"
        )

    elif rsi > 75:

        score -= 1

        reasons.append(
            f"RSI overheated ({rsi:.1f})"
        )

    # --------------------------------------------------------
    # MACD
    # --------------------------------------------------------

    if macd > 0:

        score += 1

        reasons.append(
            "MACD positive"
        )

    elif macd < 0:

        score -= 1

        reasons.append(
            "MACD negative"
        )

    # --------------------------------------------------------
    # BREAK OF STRUCTURE
    # --------------------------------------------------------

    if structure.get("bos"):

        if trend in (
            "UP",
            "LONG",
            "BULLISH"
        ):

            score += 1

            reasons.append(
                "bullish BOS"
            )

    # --------------------------------------------------------
    # BTC REGIME
    # --------------------------------------------------------

    regime = str(
        btc_regime or "UNKNOWN"
    ).upper()

    if regime == "LONG":

        score += 1

        reasons.append(
            "BTC regime supportive"
        )

    elif regime == "SHORT":

        score -= 2

        reasons.append(
            "BTC regime bearish"
        )

    # --------------------------------------------------------
    # SPOT SAFETY FILTER
    # --------------------------------------------------------

    # Spot için düşen bıçağı doğrudan satın alma.
    if trend in (
        "DOWN",
        "SHORT",
        "BEARISH"
    ):

        if score < 4:

            return {
                "symbol": symbol,
                "direction": "WAIT",
                "action": "NO_TRADE",
                "strategy": "SPOT",
                "score": score,
                "confidence": 0,
                "reason":
                    "DOWNTREND_NO_SPOT_ENTRY",
                "details": reasons,
            }

    # BTC güçlü bearish ise spot alım için
    # daha yüksek teyit gerekir.
    if regime == "SHORT" and score < 6:

        return {
            "symbol": symbol,
            "direction": "WAIT",
            "action": "NO_TRADE",
            "strategy": "SPOT",
            "score": score,
            "confidence": 0,
            "reason":
                "BTC_REGIME_NOT_SUPPORTIVE",
            "details": reasons,
        }

    # --------------------------------------------------------
    # MINIMUM SCORE
    # --------------------------------------------------------

    if score < 4:

        return {
            "symbol": symbol,
            "direction": "WAIT",
            "action": "NO_TRADE",
            "strategy": "SPOT",
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

    if regime == "SHORT":
        confidence -= 10

    confidence = max(
        0,
        min(100, confidence)
    )

    # --------------------------------------------------------
    # LEVELS
    # --------------------------------------------------------

    stop, tp1, tp2 = _levels(
        price,
        atr
    )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    return {
        "symbol": symbol,

        "direction": "LONG",
        "action": "BUY",

        "strategy": "SPOT",

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
            structure.get(
                "bos",
                False
            )
        ),

        "choch": bool(
            structure.get(
                "choch",
                False
            )
        ),

        "reason": reasons,

        "execution_mode": "PAPER",
    }


def scan_spot(
    market_data: Dict[str, Any],
    btc_regime: Optional[str] = None,
):

    results = []

    for symbol, df in (
        market_data or {}
    ).items():

        try:

            result = analyze_spot(
                df=df,
                symbol=symbol,
                btc_regime=btc_regime,
            )

            results.append(result)

        except Exception as exc:

            results.append({
                "symbol": symbol,
                "direction": "WAIT",
                "action": "NO_TRADE",
                "strategy": "SPOT",
                "score": 0,
                "confidence": 0,
                "reason":
                    f"ANALYSIS_ERROR: {exc}",
            })

    return results
