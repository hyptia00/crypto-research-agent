# ============================================================
# CRYPTO RESEARCH AGENT
# FUTURES STRATEGY ENGINE
# ============================================================

from market.indicators import (
    calculate_indicators,
    latest_indicators,
)

from market.structure import (
    analyze_structure,
)


# ============================================================
# SETTINGS
# ============================================================

MIN_SCORE = 7
MIN_RR = 2.0

ATR_STOP_MULTIPLIER = 1.5

RSI_LONG_MIN = 45
RSI_LONG_MAX = 70

RSI_SHORT_MIN = 30
RSI_SHORT_MAX = 55


# ============================================================
# HELPERS
# ============================================================

def _empty_signal(symbol):

    return {
        "symbol": symbol,
        "market": "FUTURES",
        "side": "WAIT",
        "score": 0,
        "confidence": 0,
        "reasons": [],
    }


def _trend_score(
    indicator_data,
    direction,
):
    """
    EMA trend değerlendirmesi.
    """

    if not indicator_data:
        return 0

    price = indicator_data.get(
        "price"
    )

    ema20 = indicator_data.get(
        "ema20"
    )

    ema50 = indicator_data.get(
        "ema50"
    )

    if (
        price is None
        or ema20 is None
        or ema50 is None
    ):
        return 0

    if direction == "LONG":

        if price > ema20 > ema50:
            return 2

        if price > ema20:
            return 1

        return 0

    if direction == "SHORT":

        if price < ema20 < ema50:
            return 2

        if price < ema20:
            return 1

        return 0

    return 0


def _rsi_score(
    indicator_data,
    direction,
):

    if not indicator_data:
        return 0

    value = indicator_data.get(
        "rsi"
    )

    if value is None:
        return 0

    if direction == "LONG":

        if (
            RSI_LONG_MIN
            <= value
            <= RSI_LONG_MAX
        ):
            return 1

    elif direction == "SHORT":

        if (
            RSI_SHORT_MIN
            <= value
            <= RSI_SHORT_MAX
        ):
            return 1

    return 0


def _macd_score(
    indicator_data,
    direction,
):

    if not indicator_data:
        return 0

    value = indicator_data.get(
        "macd_hist"
    )

    if value is None:
        return 0

    if direction == "LONG" and value > 0:
        return 1

    if direction == "SHORT" and value < 0:
        return 1

    return 0


def _volume_score(
    indicator_data,
):

    if not indicator_data:
        return 0

    ratio = indicator_data.get(
        "volume_ratio"
    )

    if ratio is None:
        return 0

    if ratio >= 1.5:
        return 2

    if ratio >= 1.0:
        return 1

    return 0


# ============================================================
# STRUCTURE SCORE
# ============================================================

def _structure_score(
    structure,
    direction,
):

    if not structure:
        return 0, []

    score = 0
    reasons = []

    bias = structure.get(
        "bias"
    )

    if direction == "LONG":

        if bias == "BULLISH":

            score += 2

            reasons.append(
                "Bullish market structure"
            )

    elif direction == "SHORT":

        if bias == "BEARISH":

            score += 2

            reasons.append(
                "Bearish market structure"
            )

    # --------------------------------------------------------
    # BOS
    # --------------------------------------------------------

    for event in structure.get(
        "bos",
        []
    )[-5:]:

        if event.get(
            "direction"
        ) == direction:

            score += 2

            reasons.append(
                f"{direction} BOS"
            )

            break

    # --------------------------------------------------------
    # CHoCH
    # --------------------------------------------------------

    for event in structure.get(
        "choch",
        []
    )[-5:]:

        if event.get(
            "direction"
        ) == direction:

            score += 2

            reasons.append(
                f"{direction} CHoCH"
            )

            break

    # --------------------------------------------------------
    # MSB
    # --------------------------------------------------------

    for event in structure.get(
        "msb",
        []
    )[-5:]:

        if event.get(
            "direction"
        ) == direction:

            score += 3

            reasons.append(
                f"{direction} MSB"
            )

            break

    # --------------------------------------------------------
    # LIQUIDITY SWEEP
    # --------------------------------------------------------

    for event in structure.get(
        "liquidity_sweeps",
        []
    )[-5:]:

        if event.get(
            "direction"
        ) == direction:

            score += 2

            reasons.append(
                f"{direction} liquidity sweep"
            )

            break

    # --------------------------------------------------------
    # FVG
    # --------------------------------------------------------

    for event in structure.get(
        "fvg",
        []
    )[-10:]:

        if event.get(
            "direction"
        ) == (
            "BULLISH"
            if direction == "LONG"
            else "BEARISH"
        ):

            score += 1

            reasons.append(
                "FVG"
            )

            break

    # --------------------------------------------------------
    # ORDER BLOCK
    # --------------------------------------------------------

    for event in structure.get(
        "order_blocks",
        []
    )[-10:]:

        if event.get(
            "direction"
        ) == (
            "BULLISH"
            if direction == "LONG"
            else "BEARISH"
        ):

            score += 1

            reasons.append(
                "Order Block"
            )

            break

    # --------------------------------------------------------
    # DISPLACEMENT
    # --------------------------------------------------------

    for event in structure.get(
        "displacement",
        []
    )[-5:]:

        if event.get(
            "direction"
        ) == (
            "BULLISH"
            if direction == "LONG"
            else "BEARISH"
        ):

            score += 2

            reasons.append(
                "Displacement"
            )

            break

    return score, reasons


# ============================================================
# MULTI TIMEFRAME ANALYSIS
# ============================================================

def _analyze_direction(
    direction,
    indicators,
    structures,
):

    score = 0
    reasons = []

    # ========================================================
    # 4H
    # ========================================================

    ind4 = indicators.get(
        "4h"
    )

    struct4 = structures.get(
        "4h"
    )

    trend4 = _trend_score(
        ind4,
        direction
    )

    score += trend4

    if trend4:
        reasons.append(
            "4H trend aligned"
        )

    struct_score4, struct_reasons4 = (
        _structure_score(
            struct4,
            direction
        )
    )

    # 4H structure daha ağır
    score += struct_score4

    reasons.extend(
        [
            f"4H {x}"
            for x in struct_reasons4
        ]
    )

    # ========================================================
    # 1H
    # ========================================================

    ind1 = indicators.get(
        "1h"
    )

    struct1 = structures.get(
        "1h"
    )

    trend1 = _trend_score(
        ind1,
        direction
    )

    score += trend1

    if trend1:
        reasons.append(
            "1H trend aligned"
        )

    struct_score1, struct_reasons1 = (
        _structure_score(
            struct1,
            direction
        )
    )

    score += struct_score1

    reasons.extend(
        [
            f"1H {x}"
            for x in struct_reasons1
        ]
    )

    # ========================================================
    # 15M
    # ========================================================

    ind15 = indicators.get(
        "15m"
    )

    struct15 = structures.get(
        "15m"
    )

    trend15 = _trend_score(
        ind15,
        direction
    )

    score += trend15

    if trend15:
        reasons.append(
            "15M trend aligned"
        )

    struct_score15, struct_reasons15 = (
        _structure_score(
            struct15,
            direction
        )
    )

    score += struct_score15

    reasons.extend(
        [
            f"15M {x}"
            for x in struct_reasons15
        ]
    )

    # ========================================================
    # INDICATORS
    # ========================================================

    indicator_score = 0

    rsi_score = _rsi_score(
        ind15,
        direction
    )

    indicator_score += rsi_score

    if rsi_score:
        reasons.append(
            "15M RSI confirmation"
        )

    macd_score = _macd_score(
        ind15,
        direction
    )

    indicator_score += macd_score

    if macd_score:
        reasons.append(
            "15M MACD confirmation"
        )

    volume_score = _volume_score(
        ind15
    )

    indicator_score += volume_score

    if volume_score:
        reasons.append(
            "15M volume confirmation"
        )

    score += indicator_score

    return score, reasons


# ============================================================
# ENTRY / STOP
# ============================================================

def _calculate_trade(
    symbol,
    direction,
    candles,
    indicator_data,
    structure,
):

    if candles is None:
        return None

    if candles.empty:
        return None

    price = float(
        candles.iloc[-1]["close"]
    )

    atr = indicator_data.get(
        "atr"
    )

    if atr is None or atr <= 0:
        return None

    # --------------------------------------------------------
    # SWING
    # --------------------------------------------------------

    last_swings = structure.get(
        "last_swings",
        {}
    )

    if direction == "LONG":

        swing = last_swings.get(
            "last_low"
        )

        swing_price = (
            swing.get("price")
            if swing
            else None
        )

        atr_stop = (
            price -
            atr * ATR_STOP_MULTIPLIER
        )

        if swing_price is not None:
            stop = min(
                swing_price,
                atr_stop
            )
        else:
            stop = atr_stop

        risk = price - stop

        if risk <= 0:
            return None

        tp1 = price + risk * 2
        tp2 = price + risk * 3

    else:

        swing = last_swings.get(
            "last_high"
        )

        swing_price = (
            swing.get("price")
            if swing
            else None
        )

        atr_stop = (
            price +
            atr * ATR_STOP_MULTIPLIER
        )

        if swing_price is not None:
            stop = max(
                swing_price,
                atr_stop
            )
        else:
            stop = atr_stop

        risk = stop - price

        if risk <= 0:
            return None

        tp1 = price - risk * 2
        tp2 = price - risk * 3

    rr = abs(
        tp2 - price
    ) / risk

    return {
        "symbol": symbol,
        "market": "FUTURES",
        "side": direction,
        "entry": price,
        "stop": stop,
        "tp1": tp1,
        "tp2": tp2,
        "rr": rr,
    }


# ============================================================
# PUBLIC FUNCTION
# ============================================================

def analyze_futures(
    symbol,
    data,
):

    """
    data:

    {
        "4h": DataFrame,
        "1h": DataFrame,
        "15m": DataFrame,
        "5m": DataFrame,
    }
    """

    if not data:
        return _empty_signal(
            symbol
        )

    # --------------------------------------------------------
    # INDICATORS
    # --------------------------------------------------------

    indicators = {}

    for timeframe in (
        "4h",
        "1h",
        "15m",
        "5m",
    ):

        df = data.get(
            timeframe
        )

        if df is None or df.empty:
            continue

        indicators[timeframe] = (
            latest_indicators(
                df
            )
        )

    # --------------------------------------------------------
    # STRUCTURE
    # --------------------------------------------------------

    structures = {}

    for timeframe in (
        "4h",
        "1h",
        "15m",
        "5m",
    ):

        df = data.get(
            timeframe
        )

        if df is None or df.empty:
            continue

        structures[timeframe] = (
            analyze_structure(
                calculate_indicators(
                    df
                )
            )
        )

    # --------------------------------------------------------
    # BOTH DIRECTIONS
    # --------------------------------------------------------

    long_score, long_reasons = (
        _analyze_direction(
            "LONG",
            indicators,
            structures,
        )
    )

    short_score, short_reasons = (
        _analyze_direction(
            "SHORT",
            indicators,
            structures,
        )
    )

    # --------------------------------------------------------
    # SELECT
    # --------------------------------------------------------

    if (
        long_score < MIN_SCORE
        and short_score < MIN_SCORE
    ):

        return {
            "symbol": symbol,
            "market": "FUTURES",
            "side": "WAIT",
            "score": max(
                long_score,
                short_score
            ),
            "confidence": 0,
            "reasons": [],
        }

    if long_score >= short_score:

        direction = "LONG"
        score = long_score
        reasons = long_reasons

    else:

        direction = "SHORT"
        score = short_score
        reasons = short_reasons

    # --------------------------------------------------------
    # 5M CONFIRMATION
    # --------------------------------------------------------

    struct5 = structures.get(
        "5m"
    )

    if struct5:

        bias5 = struct5.get(
            "bias"
        )

        expected = (
            "BULLISH"
            if direction == "LONG"
            else "BEARISH"
        )

        if bias5 == expected:

            score += 2

            reasons.append(
                "5M entry structure confirmed"
            )

        else:

            # 5M ters ise işlem kalitesini düşür.
            score -= 2

            reasons.append(
                "5M structure not aligned"
            )

    # --------------------------------------------------------
    # FINAL SCORE
    # --------------------------------------------------------

    if score < MIN_SCORE:

        return {
            "symbol": symbol,
            "market": "FUTURES",
            "side": "WAIT",
            "score": score,
            "confidence": 0,
            "reasons": reasons,
        }

    # --------------------------------------------------------
    # TRADE PARAMETERS
    # --------------------------------------------------------

    trade = _calculate_trade(

        symbol,

        direction,

        data.get("15m"),

        indicators.get(
            "15m",
            {}
        ),

        structures.get(
            "15m",
            {}
        ),

    )

    if trade is None:

        return _empty_signal(
            symbol
        )

    if trade["rr"] < MIN_RR:

        return {
            "symbol": symbol,
            "market": "FUTURES",
            "side": "WAIT",
            "score": score,
            "confidence": 0,
            "reasons": [
                "R/R yetersiz"
            ],
        }

    # --------------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------------

    confidence = min(
        95,
        45 + score * 4
    )

    if score >= 10:
        confidence += 5

    confidence = min(
        confidence,
        99
    )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    trade.update({

        "score":
            score,

        "confidence":
            confidence,

        "timeframe":
            "4H > 1H > 15M > 5M",

        "reasons":
            reasons,

        "status":
            "PAPER_ONLY",

    })

    return trade
