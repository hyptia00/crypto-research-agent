# ============================================================
# SCALPING ENGINE
# 15M -> 5M -> 1M
# ============================================================

from market.indicators import calculate_indicators
from market.structure import analyze_structure


def _num(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _prepare(df):

    if df is None or len(df) < 30:
        return None

    try:
        return calculate_indicators(df)
    except Exception:
        return df


def _analysis(df):

    data = _prepare(df)

    if data is None:
        return None, {}

    try:
        structure = analyze_structure(data)
    except Exception:
        structure = {}

    return data, structure


def _trend(structure):

    trend = str(
        structure.get(
            "trend",
            "UNKNOWN"
        )
    ).upper()

    if trend in (
        "BULLISH",
        "UP",
        "LONG",
    ):
        return "LONG"

    if trend in (
        "BEARISH",
        "DOWN",
        "SHORT",
    ):
        return "SHORT"

    return "UNKNOWN"


def _last(
    df,
    column,
    default=0.0
):

    if df is None:
        return default

    if column not in df.columns:
        return default

    return _num(
        df[column].iloc[-1],
        default
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
            atr * 1.5
        )

        tp2 = price + (
            atr * 2.4
        )

    else:

        stop = price + (
            atr * 1.2
        )

        tp1 = price - (
            atr * 1.5
        )

        tp2 = price - (
            atr * 2.4
        )

    return stop, tp1, tp2


# ============================================================
# MAIN
# ============================================================

def analyze_scalping(
    data,
    symbol,
    btc_regime=None,
):

    symbol = str(
        symbol
    ).upper()

    # --------------------------------------------------------
    # TIMEFRAMES
    # --------------------------------------------------------

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
            "action": "NO_TRADE",
            "strategy": "SCALPING",
            "score": 0,
            "confidence": 0,
            "reason":
                "MISSING_TIMEFRAME",
        }

    # ========================================================
    # 15M
    # DIRECTION / MARKET STRUCTURE
    # ========================================================

    data15, s15 = _analysis(
        df15
    )

    data5, s5 = _analysis(
        df5
    )

    data1, s1 = _analysis(
        df1
    )

    if (
        data15 is None
        or data5 is None
        or data1 is None
    ):

        return {
            "symbol": symbol,
            "direction": "WAIT",
            "action": "NO_TRADE",
            "strategy": "SCALPING",
            "score": 0,
            "confidence": 0,
            "reason":
                "INSUFFICIENT_DATA",
        }

    direction15 = _trend(
        s15
    )

    direction5 = _trend(
        s5
    )

    direction1 = _trend(
        s1
    )

    # 15M ana yön vermiyorsa işlem yok.
    if direction15 == "UNKNOWN":

        return {
            "symbol": symbol,
            "direction": "WAIT",
            "action": "NO_TRADE",
            "strategy": "SCALPING",
            "score": 0,
            "confidence": 0,
            "reason":
                "15M_NO_DIRECTION",
        }

    direction = direction15

    score = 0
    reasons = []

    # ========================================================
    # 15M CONFIRMATION
    # ========================================================

    score += 2

    reasons.append(
        f"15M direction: {direction15}"
    )

    if direction == "LONG":

        if s15.get(
            "bullish_bos"
        ):

            score += 2

            reasons.append(
                "15M bullish BOS"
            )

        if s15.get(
            "bullish_msb"
        ):

            score += 3

            reasons.append(
                "15M bullish MSB"
            )

        if s15.get(
            "bullish_choch"
        ):

            score += 2

            reasons.append(
                "15M bullish CHoCH"
            )

        if s15.get(
            "bullish_sweep"
        ):

            score += 2

            reasons.append(
                "15M sell-side sweep"
            )

    else:

        if s15.get(
            "bearish_bos"
        ):

            score += 2

            reasons.append(
                "15M bearish BOS"
            )

        if s15.get(
            "bearish_msb"
        ):

            score += 3

            reasons.append(
                "15M bearish MSB"
            )

        if s15.get(
            "bearish_choch"
        ):

            score += 2

            reasons.append(
                "15M bearish CHoCH"
            )

        if s15.get(
            "bearish_sweep"
        ):

            score += 2

            reasons.append(
                "15M buy-side sweep"
            )

    # ========================================================
    # 5M SETUP
    # ========================================================

    if direction5 != direction:

        return {
            "symbol": symbol,
            "direction": "WAIT",
            "action": "NO_TRADE",
            "strategy": "SCALPING",
            "score": score,
            "confidence": 0,
            "reason":
                "5M_DIRECTION_MISMATCH",
        }

    score += 2

    reasons.append(
        "5M aligned"
    )

    if direction == "LONG":

        if s5.get(
            "bullish_bos"
        ):

            score += 2

            reasons.append(
                "5M bullish BOS"
            )

        if s5.get(
            "bullish_msb"
        ):

            score += 3

            reasons.append(
                "5M bullish MSB"
            )

        if s5.get(
            "bullish_choch"
        ):

            score += 2

            reasons.append(
                "5M bullish CHoCH"
            )

        if s5.get(
            "bullish_sweep"
        ):

            score += 3

            reasons.append(
                "5M sell-side sweep"
            )

    else:

        if s5.get(
            "bearish_bos"
        ):

            score += 2

            reasons.append(
                "5M bearish BOS"
            )

        if s5.get(
            "bearish_msb"
        ):

            score += 3

            reasons.append(
                "5M bearish MSB"
            )

        if s5.get(
            "bearish_choch"
        ):

            score += 2

            reasons.append(
                "5M bearish CHoCH"
            )

        if s5.get(
            "bearish_sweep"
        ):

            score += 3

            reasons.append(
                "5M buy-side sweep"
            )

    # ========================================================
    # 1M ENTRY TRIGGER
    # ========================================================

    if direction1 != direction:

        return {
            "symbol": symbol,
            "direction": "WAIT",
            "action": "NO_TRADE",
            "strategy": "SCALPING",
            "score": score,
            "confidence": 0,
            "reason":
                "1M_DIRECTION_MISMATCH",
        }

    score += 2

    reasons.append(
        "1M aligned"
    )

    trigger = False

    if direction == "LONG":

        if s1.get(
            "bullish_bos"
        ):

            trigger = True

            score += 3

            reasons.append(
                "1M bullish BOS trigger"
            )

        if s1.get(
            "bullish_msb"
        ):

            trigger = True

            score += 3

            reasons.append(
                "1M bullish MSB trigger"
            )

        if s1.get(
            "bullish_choch"
        ):

            trigger = True

            score += 3

            reasons.append(
                "1M bullish CHoCH trigger"
            )

        if s1.get(
            "bullish_sweep"
        ):

            trigger = True

            score += 3

            reasons.append(
                "1M sell-side sweep"
            )

    else:

        if s1.get(
            "bearish_bos"
        ):

            trigger = True

            score += 3

            reasons.append(
                "1M bearish BOS trigger"
            )

        if s1.get(
            "bearish_msb"
        ):

            trigger = True

            score += 3

            reasons.append(
                "1M bearish MSB trigger"
            )

        if s1.get(
            "bearish_choch"
        ):

            trigger = True

            score += 3

            reasons.append(
                "1M bearish CHoCH trigger"
            )

        if s1.get(
            "bearish_sweep"
        ):

            trigger = True

            score += 3

            reasons.append(
                "1M buy-side sweep"
            )

    # 1M'de trigger yoksa scalping işlemi yok.
    if not trigger:

        return {
            "symbol": symbol,
            "direction": "WAIT",
            "action": "NO_TRADE",
            "strategy": "SCALPING",
            "score": score,
            "confidence": 0,
            "reason":
                "NO_1M_STRUCTURE_TRIGGER",
        }

    # ========================================================
    # 1M MOMENTUM
    # ========================================================

    rsi = _last(
        data1,
        "rsi"
    )

    macd_hist = _last(
        data1,
        "macd_hist"
    )

    volume_ratio = _last(
        data1,
        "volume_ratio",
        1.0
    )

    if direction == "LONG":

        if 45 <= rsi <= 70:

            score += 1

            reasons.append(
                "1M RSI confirms LONG"
            )

        if macd_hist > 0:

            score += 1

            reasons.append(
                "1M MACD confirms LONG"
            )

    else:

        if 30 <= rsi <= 55:

            score += 1

            reasons.append(
                "1M RSI confirms SHORT"
            )

        if macd_hist < 0:

            score += 1

            reasons.append(
                "1M MACD confirms SHORT"
            )

    if volume_ratio >= 1.5:

        score += 2

        reasons.append(
            "volume expansion"
        )

    # ========================================================
    # BTC REGIME
    # ========================================================

    regime = str(
        btc_regime or "UNKNOWN"
    ).upper()

    if regime == direction:

        score += 2

        reasons.append(
            "BTC regime aligned"
        )

    elif regime in (
        "LONG",
        "SHORT",
    ):

        score -= 3

        reasons.append(
            "BTC regime against trade"
        )

    # ========================================================
    # MINIMUM SCORE
    # ========================================================

    if score < 10:

        return {
            "symbol": symbol,
            "direction": "WAIT",
            "action": "NO_TRADE",
            "strategy": "SCALPING",
            "score": score,
            "confidence": 0,
            "reason":
                "SCALPING_SCORE_TOO_LOW",
            "details": reasons,
        }

    # ========================================================
    # PRICE / ATR
    # ========================================================

    price = _last(
        data1,
        "close"
    )

    atr = _last(
        data1,
        "atr"
    )

    if price <= 0:

        return {
            "symbol": symbol,
            "direction": "WAIT",
            "action": "NO_TRADE",
            "strategy": "SCALPING",
            "score": score,
            "confidence": 0,
            "reason":
                "INVALID_PRICE",
        }

    stop, tp1, tp2 = _levels(
        price,
        atr,
        direction
    )

    # ========================================================
    # R/R
    # ========================================================

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
            "strategy": "SCALPING",
            "score": score,
            "confidence": 0,
            "reason":
                "INVALID_STOP",
        }

    rr = reward / risk

    if rr < 1.5:

        return {
            "symbol": symbol,
            "direction": "WAIT",
            "action": "NO_TRADE",
            "strategy": "SCALPING",
            "score": score,
            "confidence": 0,
            "reason":
                "SCALPING_RR_TOO_LOW",
        }

    # ========================================================
    # CONFIDENCE
    # ========================================================

    confidence = min(
        98,
        50 + score * 3
    )

    # Üç timeframe aynı yönde
    if (
        direction15 == direction
        and direction5 == direction
        and direction1 == direction
    ):

        confidence += 5

    confidence = min(
        99,
        confidence
    )

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
            "SCALPING",

        "timeframe":
            "15M > 5M > 1M",

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

        "trend15":
            direction15,

        "trend5":
            direction5,

        "trend1":
            direction1,

        "rsi":
            rsi,

        "macd_hist":
            macd_hist,

        "volume_ratio":
            volume_ratio,

        "atr":
            atr,

        "msb":
            bool(
                s15.get("msb")
                or s5.get("msb")
                or s1.get("msb")
            ),

        "choch":
            bool(
                s15.get("choch")
                or s5.get("choch")
                or s1.get("choch")
            ),

        "liquidity_sweep":
            bool(
                s15.get("liquidity_sweep")
                or s5.get("liquidity_sweep")
                or s1.get("liquidity_sweep")
            ),

        "fvg":
            s5.get("fvg")
            or s1.get("fvg"),

        "reasons":
            reasons,

        "execution_mode":
            "PAPER",

    }


def scan_scalping(
    market_data,
    btc_regime=None,
):

    results = []

    for symbol, data in (
        market_data or {}
    ).items():

        try:

            results.append(
                analyze_scalping(
                    data=data,
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
                    "SCALPING",

                "score":
                    0,

                "confidence":
                    0,

                "reason":
                    f"ANALYSIS_ERROR: {exc}",

            })

    return results
