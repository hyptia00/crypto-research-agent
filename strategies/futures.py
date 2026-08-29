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


def _last(df, column, default=0.0):

    if df is None or len(df) == 0:
        return default

    if column not in df.columns:
        return default

    return _float(
        df[column].iloc[-1],
        default
    )


def _levels(
    price,
    atr,
    direction,
):

    if atr <= 0:
        atr = price * 0.01

    if direction == "LONG":

        stop = price - atr * 1.5
        tp1 = price + atr * 2.0
        tp2 = price + atr * 3.0

    else:

        stop = price + atr * 1.5
        tp1 = price - atr * 2.0
        tp2 = price - atr * 3.0

    return stop, tp1, tp2


def analyze_futures(
    df,
    symbol: str,
    btc_regime: Optional[str] = None,
):

    symbol = symbol.upper()

    if df is None or len(df) < 50:

        return {
            "symbol": symbol,
            "direction": "WAIT",
            "action": "NO_TRADE",
            "strategy": "FUTURES",
            "score": 0,
            "confidence": 0,
            "reason": "INSUFFICIENT_DATA",
        }

    # ========================================================
    # INDICATORS
    # ========================================================

    try:
        data = calculate_indicators(df)
    except Exception:

        data = df.copy()

    # ========================================================
    # STRUCTURE
    # ========================================================

    try:
        structure = analyze_structure(data)
    except Exception:

        structure = {}

    price = _last(
        data,
        "close"
    )

    ema20 = _last(
        data,
        "ema20"
    )

    ema50 = _last(
        data,
        "ema50"
    )

    rsi = _last(
        data,
        "rsi"
    )

    macd_hist = _last(
        data,
        "macd_hist"
    )

    atr = _last(
        data,
        "atr"
    )

    volume_ratio = _last(
        data,
        "volume_ratio",
        1.0
    )

    # ========================================================
    # STRUCTURE FLAGS
    # ========================================================

    trend = str(
        structure.get(
            "trend",
            "UNKNOWN"
        )
    ).upper()

    bullish_bos = bool(
        structure.get(
            "bullish_bos",
            False
        )
    )

    bearish_bos = bool(
        structure.get(
            "bearish_bos",
            False
        )
    )

    bullish_msb = bool(
        structure.get(
            "bullish_msb",
            False
        )
    )

    bearish_msb = bool(
        structure.get(
            "bearish_msb",
            False
        )
    )

    bullish_choch = bool(
        structure.get(
            "bullish_choch",
            False
        )
    )

    bearish_choch = bool(
        structure.get(
            "bearish_choch",
            False
        )
    )

    bullish_sweep = bool(
        structure.get(
            "bullish_sweep",
            False
        )
    )

    bearish_sweep = bool(
        structure.get(
            "bearish_sweep",
            False
        )
    )

    fvg = structure.get(
        "fvg"
    )

    # ========================================================
    # SCORES
    # ========================================================

    long_score = 0
    short_score = 0

    long_reasons = []
    short_reasons = []

    # ========================================================
    # TREND
    # ========================================================

    if trend == "BULLISH":

        long_score += 2

        long_reasons.append(
            "bullish market structure"
        )

    elif trend == "BEARISH":

        short_score += 2

        short_reasons.append(
            "bearish market structure"
        )

    # ========================================================
    # EMA
    # ========================================================

    if (
        price > ema20
        and ema20 > ema50
    ):

        long_score += 2

        long_reasons.append(
            "EMA trend bullish"
        )

    elif (
        price < ema20
        and ema20 < ema50
    ):

        short_score += 2

        short_reasons.append(
            "EMA trend bearish"
        )

    # ========================================================
    # RSI
    # ========================================================

    if 50 <= rsi <= 68:

        long_score += 1

        long_reasons.append(
            f"RSI bullish ({rsi:.1f})"
        )

    elif 32 <= rsi <= 50:

        short_score += 1

        short_reasons.append(
            f"RSI bearish ({rsi:.1f})"
        )

    # ========================================================
    # MACD
    # ========================================================

    if macd_hist > 0:

        long_score += 1

        long_reasons.append(
            "MACD momentum bullish"
        )

    elif macd_hist < 0:

        short_score += 1

        short_reasons.append(
            "MACD momentum bearish"
        )

    # ========================================================
    # VOLUME
    # ========================================================

    if volume_ratio >= 1.5:

        if long_score >= short_score:

            long_score += 1

            long_reasons.append(
                "volume expansion"
            )

        else:

            short_score += 1

            short_reasons.append(
                "volume expansion"
            )

    # ========================================================
    # BOS
    # ========================================================

    if bullish_bos:

        long_score += 2

        long_reasons.append(
            "bullish BOS"
        )

    if bearish_bos:

        short_score += 2

        short_reasons.append(
            "bearish BOS"
        )

    # ========================================================
    # MSB
    # ========================================================

    if bullish_msb:

        long_score += 3

        long_reasons.append(
            "bullish MSB"
        )

    if bearish_msb:

        short_score += 3

        short_reasons.append(
            "bearish MSB"
        )

    # ========================================================
    # CHoCH
    # ========================================================

    if bullish_choch:

        long_score += 3

        long_reasons.append(
            "bullish CHoCH"
        )

    if bearish_choch:

        short_score += 3

        short_reasons.append(
            "bearish CHoCH"
        )

    # ========================================================
    # LIQUIDITY SWEEP
    # ========================================================

    if bullish_sweep:

        long_score += 3

        long_reasons.append(
            "sell-side liquidity sweep"
        )

    if bearish_sweep:

        short_score += 3

        short_reasons.append(
            "buy-side liquidity sweep"
        )

    # ========================================================
    # FVG
    # ========================================================

    if isinstance(fvg, dict):

        fvg_type = str(
            fvg.get(
                "type",
                ""
            )
        ).upper()

        if fvg_type == "BULLISH":

            long_score += 2

            long_reasons.append(
                "bullish FVG"
            )

        elif fvg_type == "BEARISH":

            short_score += 2

            short_reasons.append(
                "bearish FVG"
            )

    # ========================================================
    # BTC REGIME
    # ========================================================

    regime = str(
        btc_regime or "UNKNOWN"
    ).upper()

    if regime == "LONG":

        long_score += 1

        short_score -= 1

    elif regime == "SHORT":

        short_score += 1

        long_score -= 1

    # ========================================================
    # DIRECTION
    # ========================================================

    if long_score > short_score:

        direction = "LONG"
        score = long_score
        reasons = long_reasons

    elif short_score > long_score:

        direction = "SHORT"
        score = short_score
        reasons = short_reasons

    else:

        return {
            "symbol": symbol,
            "direction": "WAIT",
            "action": "NO_TRADE",
            "strategy": "FUTURES",
            "score": 0,
            "confidence": 0,
            "reason":
                "LONG_SHORT_CONFLICT",
        }

    # ========================================================
    # MINIMUM SCORE
    # ========================================================

    if score < 5:

        return {
            "symbol": symbol,
            "direction": "WAIT",
            "action": "NO_TRADE",
            "strategy": "FUTURES",
            "score": score,
            "confidence": 0,
            "reason":
                "INSUFFICIENT_CONFIRMATION",
            "details": reasons,
        }

    # ========================================================
    # CONFIDENCE
    # ========================================================

    confidence = min(
        96,
        45 + score * 6
    )

    # BTC ters yöndeyse güven azalt
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

    # ========================================================
    # LEVELS
    # ========================================================

    stop, tp1, tp2 = _levels(
        price,
        atr,
        direction
    )

    risk = abs(
        price - stop
    )

    reward = abs(
        tp2 - price
    )

    if risk <= 0:

        return {
            "symbol": symbol,
            "direction": "WAIT",
            "action": "NO_TRADE",
            "strategy": "FUTURES",
            "score": score,
            "confidence": 0,
            "reason":
                "INVALID_RISK",
        }

    rr = reward / risk

    # ========================================================
    # RESULT
    # ========================================================

    return {

        "symbol":
            symbol,

        "direction":
            direction,

        "action":
            direction,

        "strategy":
            "FUTURES",

        "score":
            score,

        "confidence":
            round(
                confidence,
                1
            ),

        "entry":
            price,

        "price":
            price,

        "stop":
            stop,

        "tp1":
            tp1,

        "tp2":
            tp2,

        "rr":
            round(
                rr,
                2
            ),

        "btc_regime":
            regime,

        "trend":
            trend,

        "rsi":
            rsi,

        "macd_hist":
            macd_hist,

        "atr":
            atr,

        "volume_ratio":
            volume_ratio,

        "bos":
            (
                bullish_bos
                or
                bearish_bos
            ),

        "msb":
            (
                bullish_msb
                or
                bearish_msb
            ),

        "choch":
            (
                bullish_choch
                or
                bearish_choch
            ),

        "liquidity_sweep":
            (
                bullish_sweep
                or
                bearish_sweep
            ),

        "fvg":
            fvg,

        "reasons":
            reasons,

        "execution_mode":
            "PAPER",

    }


def scan_futures(
    market_data,
    btc_regime=None,
):

    results = []

    for symbol, df in (
        market_data or {}
    ).items():

        try:

            results.append(
                analyze_futures(
                    df=df,
                    symbol=symbol,
                    btc_regime=btc_regime,
                )
            )

        except Exception as exc:

            results.append({

                "symbol":
                    symbol,

                "direction":
                    "WAIT",

                "action":
                    "NO_TRADE",

                "strategy":
                    "FUTURES",

                "score":
                    0,

                "confidence":
                    0,

                "reason":
                    f"ANALYSIS_ERROR: {exc}",

            })

    return results
