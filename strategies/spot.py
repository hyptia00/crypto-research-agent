# ============================================================
# CRYPTO RESEARCH AGENT
# SPOT STRATEGY ENGINE
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

RSI_MIN = 40
RSI_MAX = 70


# ============================================================
# EMPTY SIGNAL
# ============================================================

def _wait(symbol, score=0, reasons=None):

    return {
        "symbol": symbol,
        "market": "SPOT",
        "side": "WAIT",
        "score": score,
        "confidence": 0,
        "reasons": reasons or [],
    }


# ============================================================
# TREND
# ============================================================

def _trend_score(indicator_data):

    if not indicator_data:
        return 0

    price = indicator_data.get("price")
    ema20 = indicator_data.get("ema20")
    ema50 = indicator_data.get("ema50")

    if (
        price is None
        or ema20 is None
        or ema50 is None
    ):
        return 0

    if price > ema20 > ema50:
        return 3

    if price > ema20:
        return 1

    return 0


# ============================================================
# RSI
# ============================================================

def _rsi_score(indicator_data):

    if not indicator_data:
        return 0

    value = indicator_data.get("rsi")

    if value is None:
        return 0

    if RSI_MIN <= value <= RSI_MAX:
        return 1

    return 0


# ============================================================
# MACD
# ============================================================

def _macd_score(indicator_data):

    if not indicator_data:
        return 0

    histogram = indicator_data.get(
        "macd_hist"
    )

    if histogram is None:
        return 0

    if histogram > 0:
        return 1

    return 0


# ============================================================
# VOLUME
# ============================================================

def _volume_score(indicator_data):

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
# STRUCTURE
# ============================================================

def _structure_score(structure):

    if not structure:
        return 0, []

    score = 0
    reasons = []

    # --------------------------------------------------------
    # BIAS
    # --------------------------------------------------------

    bias = structure.get(
        "bias"
    )

    if bias == "BULLISH":

        score += 2

        reasons.append(
            "Bullish market structure"
        )

    elif bias == "BEARISH":

        # Spot için bearish yapı ciddi negatif.
        score -= 3

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
        ) == "BULLISH":

            score += 2

            reasons.append(
                "Bullish BOS"
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
        ) == "BULLISH":

            score += 2

            reasons.append(
                "Bullish CHoCH"
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
        ) == "BULLISH":

            score += 3

            reasons.append(
                "Bullish MSB"
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
        ) == "BULLISH":

            score += 2

            reasons.append(
                "Sell-side liquidity sweep"
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
        ) == "BULLISH":

            score += 1

            reasons.append(
                "Bullish FVG"
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
        ) == "BULLISH":

            score += 1

            reasons.append(
                "Bullish Order Block"
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
        ) == "BULLISH":

            score += 2

            reasons.append(
                "Bullish displacement"
            )

            break

    return score, reasons


# ============================================================
# TRADE PARAMETERS
# ============================================================

def _calculate_trade(
    symbol,
    candles,
    indicators,
    structure,
):

    if candles is None or candles.empty:
        return None

    price = float(
        candles.iloc[-1]["close"]
    )

    atr = indicators.get(
        "atr"
    )

    if atr is None or atr <= 0:
        return None

    # --------------------------------------------------------
    # LAST SWING LOW
    # --------------------------------------------------------

    last_swings = structure.get(
        "last_swings",
        {}
    )

    swing_low = last_swings.get(
        "last_low"
    )

    swing_price = None

    if swing_low:

        swing_price = swing_low.get(
            "price"
        )

    # --------------------------------------------------------
    # STOP
    # --------------------------------------------------------

    atr_stop = (
        price -
        atr * ATR_STOP_MULTIPLIER
    )

    if swing_price is not None:

        stop = min(
            float(swing_price),
            atr_stop
        )

    else:

        stop = atr_stop

    risk = price - stop

    if risk <= 0:
        return None

    # --------------------------------------------------------
    # TARGETS
    # --------------------------------------------------------

    tp1 = price + risk * 2

    tp2 = price + risk * 3

    rr = (
        abs(tp2 - price)
        / risk
    )

    if rr < MIN_RR:
        return None

    return {
        "symbol": symbol,
        "market": "SPOT",
        "side": "BUY",
        "entry": price,
        "stop": stop,
        "tp1": tp1,
        "tp2": tp2,
        "rr": rr,
    }


# ============================================================
# PUBLIC FUNCTION
# ============================================================

def analyze_spot(
    symbol,
    data,
):

    """
    data:

    {
        "4h": DataFrame,
        "1h": DataFrame,
        "15m": DataFrame,
    }

    Spot tarafında yalnızca BUY üretilir.
    """

    if not data:
        return _wait(symbol)

    # ========================================================
    # DATA
    # ========================================================

    df4 = data.get("4h")
    df1 = data.get("1h")
    df15 = data.get("15m")

    if (
        df4 is None
        or df1 is None
        or df15 is None
    ):
        return _wait(
            symbol,
            reasons=[
                "Eksik timeframe verisi"
            ]
        )

    if (
        df4.empty
        or df1.empty
        or df15.empty
    ):
        return _wait(
            symbol,
            reasons=[
                "Boş timeframe verisi"
            ]
        )

    # ========================================================
    # INDICATORS
    # ========================================================

    ind4 = latest_indicators(
        df4
    )

    ind1 = latest_indicators(
        df1
    )

    ind15 = latest_indicators(
        df15
    )

    # ========================================================
    # STRUCTURE
    # ========================================================

    struct4 = analyze_structure(
        calculate_indicators(
            df4
        )
    )

    struct1 = analyze_structure(
        calculate_indicators(
            df1
        )
    )

    struct15 = analyze_structure(
        calculate_indicators(
            df15
        )
    )

    # ========================================================
    # SCORE
    # ========================================================

    score = 0
    reasons = []

    # --------------------------------------------------------
    # 4H TREND
    # --------------------------------------------------------

    trend4 = _trend_score(
        ind4
    )

    score += trend4

    if trend4 >= 3:

        reasons.append(
            "4H bullish trend"
        )

    elif trend4 == 1:

        reasons.append(
            "4H price above EMA20"
        )

    # --------------------------------------------------------
    # 4H STRUCTURE
    # --------------------------------------------------------

    struct_score4, struct_reasons4 = (
        _structure_score(
            struct4
        )
    )

    score += struct_score4

    reasons.extend(
        [
            f"4H {reason}"
            for reason in struct_reasons4
        ]
    )

    # --------------------------------------------------------
    # 1H TREND
    # --------------------------------------------------------

    trend1 = _trend_score(
        ind1
    )

    score += trend1

    if trend1 >= 3:

        reasons.append(
            "1H bullish trend"
        )

    elif trend1 == 1:

        reasons.append(
            "1H price above EMA20"
        )

    # --------------------------------------------------------
    # 1H STRUCTURE
    # --------------------------------------------------------

    struct_score1, struct_reasons1 = (
        _structure_score(
            struct1
        )
    )

    score += struct_score1

    reasons.extend(
        [
            f"1H {reason}"
            for reason in struct_reasons1
        ]
    )

    # --------------------------------------------------------
    # 15M SETUP
    # --------------------------------------------------------

    struct_score15, struct_reasons15 = (
        _structure_score(
            struct15
        )
    )

    score += struct_score15

    reasons.extend(
        [
            f"15M {reason}"
            for reason in struct_reasons15
        ]
    )

    # --------------------------------------------------------
    # INDICATORS
    # --------------------------------------------------------

    rsi_score = _rsi_score(
        ind15
    )

    score += rsi_score

    if rsi_score:
        reasons.append(
            "15M RSI confirmation"
        )

    macd_score = _macd_score(
        ind15
    )

    score += macd_score

    if macd_score:
        reasons.append(
            "15M MACD confirmation"
        )

    volume_score = _volume_score(
        ind15
    )

    score += volume_score

    if volume_score:
        reasons.append(
            "15M volume confirmation"
        )

    # ========================================================
    # BEARISH FILTER
    # ========================================================

    if (
        struct4.get("bias")
        == "BEARISH"
    ):

        return _wait(
            symbol,
            score,
            reasons + [
                "4H bearish: spot BUY engellendi"
            ]
        )

    # ========================================================
    # MINIMUM SCORE
    # ========================================================

    if score < MIN_SCORE:

        return _wait(
            symbol,
            score,
            reasons
        )

    # ========================================================
    # TRADE
    # ========================================================

    trade = _calculate_trade(

        symbol,

        df15,

        ind15,

        struct15,

    )

    if trade is None:

        return _wait(
            symbol,
            score,
            reasons + [
                "Uygun R/R veya SL bulunamadı"
            ]
        )

    # ========================================================
    # CONFIDENCE
    # ========================================================

    confidence = min(
        95,
        45 + score * 4
    )

    if (
        struct4.get("bias")
        == "BULLISH"
        and struct1.get("bias")
        == "BULLISH"
    ):

        confidence += 5

    confidence = min(
        confidence,
        99
    )

    # ========================================================
    # RESULT
    # ========================================================

    trade.update({

        "score":
            score,

        "confidence":
            confidence,

        "timeframe":
            "4H > 1H > 15M",

        "status":
            "PAPER_ONLY",

        "reasons":
            reasons,

    })

    return trade
