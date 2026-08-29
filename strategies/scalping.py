# ============================================================
# CRYPTO RESEARCH AGENT
# SCALPING STRATEGY ENGINE
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

MIN_SCORE = 8

MIN_RR = 1.5

ATR_STOP_MULTIPLIER = 1.2


# ============================================================
# WAIT SIGNAL
# ============================================================

def _wait(
    symbol,
    score=0,
    reasons=None,
):

    return {
        "symbol": symbol,
        "market": "SCALPING",
        "side": "WAIT",
        "score": score,
        "confidence": 0,
        "reasons": reasons or [],
    }


# ============================================================
# TREND
# ============================================================

def _trend(
    indicators,
):

    if not indicators:
        return "UNKNOWN"

    price = indicators.get(
        "price"
    )

    ema20 = indicators.get(
        "ema20"
    )

    ema50 = indicators.get(
        "ema50"
    )

    if (
        price is None
        or ema20 is None
        or ema50 is None
    ):
        return "UNKNOWN"

    if price > ema20 > ema50:
        return "BULLISH"

    if price < ema20 < ema50:
        return "BEARISH"

    return "SIDEWAYS"


# ============================================================
# MOMENTUM
# ============================================================

def _momentum(
    indicators,
    direction,
):

    if not indicators:
        return 0

    score = 0

    rsi = indicators.get(
        "rsi"
    )

    macd_hist = indicators.get(
        "macd_hist"
    )

    volume_ratio = indicators.get(
        "volume_ratio"
    )

    # --------------------------------------------------------
    # RSI
    # --------------------------------------------------------

    if direction == "LONG":

        if (
            rsi is not None
            and 45 <= rsi <= 70
        ):
            score += 1

    elif direction == "SHORT":

        if (
            rsi is not None
            and 30 <= rsi <= 55
        ):
            score += 1

    # --------------------------------------------------------
    # MACD
    # --------------------------------------------------------

    if macd_hist is not None:

        if (
            direction == "LONG"
            and macd_hist > 0
        ):
            score += 1

        elif (
            direction == "SHORT"
            and macd_hist < 0
        ):
            score += 1

    # --------------------------------------------------------
    # VOLUME
    # --------------------------------------------------------

    if volume_ratio is not None:

        if volume_ratio >= 1.2:
            score += 1

    return score


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

    expected = (
        "BULLISH"
        if direction == "LONG"
        else "BEARISH"
    )

    # --------------------------------------------------------
    # BIAS
    # --------------------------------------------------------

    bias = structure.get(
        "bias"
    )

    if bias == expected:

        score += 2

        reasons.append(
            f"{direction} structure"
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
        ) == expected:

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
        ) == expected:

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
        ) == expected:

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
        ) == expected:

            score += 2

            reasons.append(
                f"{direction} liquidity sweep"
            )

            break

    # --------------------------------------------------------
    # FVG
    # --------------------------------------------------------

    expected_fvg = expected

    for event in structure.get(
        "fvg",
        []
    )[-10:]:

        if event.get(
            "direction"
        ) == expected_fvg:

            score += 1

            reasons.append(
                f"{direction} FVG"
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
        ) == expected:

            score += 1

            reasons.append(
                f"{direction} Order Block"
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
        ) == expected:

            score += 2

            reasons.append(
                f"{direction} displacement"
            )

            break

    return score, reasons


# ============================================================
# 1M ENTRY TRIGGER
# ============================================================

def _entry_trigger(
    structure_1m,
    indicators_1m,
    direction,
):

    score = 0
    reasons = []

    expected = (
        "BULLISH"
        if direction == "LONG"
        else "BEARISH"
    )

    # --------------------------------------------------------
    # STRUCTURE
    # --------------------------------------------------------

    if structure_1m:

        bias = structure_1m.get(
            "bias"
        )

        if bias == expected:

            score += 2

            reasons.append(
                "1M structure aligned"
            )

        # ----------------------------------------------------
        # MSB
        # ----------------------------------------------------

        for event in structure_1m.get(
            "msb",
            []
        )[-3:]:

            if event.get(
                "direction"
            ) == expected:

                score += 3

                reasons.append(
                    "1M MSB trigger"
                )

                break

        # ----------------------------------------------------
        # BOS
        # ----------------------------------------------------

        for event in structure_1m.get(
            "bos",
            []
        )[-3:]:

            if event.get(
                "direction"
            ) == expected:

                score += 2

                reasons.append(
                    "1M BOS trigger"
                )

                break

        # ----------------------------------------------------
        # LIQUIDITY SWEEP
        # ----------------------------------------------------

        for event in structure_1m.get(
            "liquidity_sweeps",
            []
        )[-3:]:

            if event.get(
                "direction"
            ) == expected:

                score += 3

                reasons.append(
                    "1M liquidity sweep"
                )

                break

    # --------------------------------------------------------
    # EMA
    # --------------------------------------------------------

    if indicators_1m:

        trend = _trend(
            indicators_1m
        )

        if (
            direction == "LONG"
            and trend == "BULLISH"
        ):

            score += 1

            reasons.append(
                "1M EMA aligned"
            )

        elif (
            direction == "SHORT"
            and trend == "BEARISH"
        ):

            score += 1

            reasons.append(
                "1M EMA aligned"
            )

    return score, reasons


# ============================================================
# TRADE PARAMETERS
# ============================================================

def _trade_parameters(
    symbol,
    candles,
    indicators,
    structure,
    direction,
):

    if candles is None:
        return None

    if candles.empty:
        return None

    price = float(
        candles.iloc[-1]["close"]
    )

    atr = indicators.get(
        "atr"
    )

    if atr is None or atr <= 0:
        return None

    last_swings = structure.get(
        "last_swings",
        {}
    )

    # ========================================================
    # LONG
    # ========================================================

    if direction == "LONG":

        swing = last_swings.get(
            "last_low"
        )

        swing_price = None

        if swing:
            swing_price = swing.get(
                "price"
            )

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

        tp1 = price + risk * 1.5
        tp2 = price + risk * 2.0

    # ========================================================
    # SHORT
    # ========================================================

    else:

        swing = last_swings.get(
            "last_high"
        )

        swing_price = None

        if swing:
            swing_price = swing.get(
                "price"
            )

        atr_stop = (
            price +
            atr * ATR_STOP_MULTIPLIER
        )

        if swing_price is not None:

            stop = max(
                float(swing_price),
                atr_stop
            )

        else:

            stop = atr_stop

        risk = stop - price

        if risk <= 0:
            return None

        tp1 = price - risk * 1.5
        tp2 = price - risk * 2.0

    rr = abs(
        tp2 - price
    ) / risk

    if rr < MIN_RR:
        return None

    return {
        "symbol": symbol,
        "market": "SCALPING",
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

def analyze_scalping(
    symbol,
    data,
):

    """
    Scalping sistemi:

        15M = ana yön
         ↓
         5M = setup
         ↓
         1M = entry trigger

    """

    if not data:
        return _wait(symbol)

    df15 = data.get(
        "15m"
    )

    df5 = data.get(
        "5m"
    )

    df1 = data.get(
        "1m"
    )

    if (
        df15 is None
        or df5 is None
        or df1 is None
    ):

        return _wait(
            symbol,
            reasons=[
                "15M/5M/1M verisi eksik"
            ]
        )

    if (
        df15.empty
        or df5.empty
        or df1.empty
    ):

        return _wait(
            symbol,
            reasons=[
                "Scalping verisi boş"
            ]
        )

    # ========================================================
    # INDICATORS
    # ========================================================

    ind15 = latest_indicators(
        df15
    )

    ind5 = latest_indicators(
        df5
    )

    ind1 = latest_indicators(
        df1
    )

    # ========================================================
    # STRUCTURE
    # ========================================================

    struct15 = analyze_structure(
        calculate_indicators(
            df15
        )
    )

    struct5 = analyze_structure(
        calculate_indicators(
            df5
        )
    )

    struct1 = analyze_structure(
        calculate_indicators(
            df1
        )
    )

    # ========================================================
    # 15M DIRECTION
    # ========================================================

    trend15 = _trend(
        ind15
    )

    if trend15 == "SIDEWAYS":

        return _wait(
            symbol,
            reasons=[
                "15M yön belirsiz"
            ]
        )

    if trend15 == "UNKNOWN":

        return _wait(
            symbol,
            reasons=[
                "15M trend hesaplanamadı"
            ]
        )

    if trend15 == "BULLISH":

        direction = "LONG"

    else:

        direction = "SHORT"

    # ========================================================
    # 15M STRUCTURE
    # ========================================================

    score = 0
    reasons = []

    structure_score15, structure_reasons15 = (
        _structure_score(
            struct15,
            direction
        )
    )

    score += structure_score15

    reasons.extend(
        [
            f"15M {x}"
            for x in structure_reasons15
        ]
    )

    # ========================================================
    # 15M MOMENTUM
    # ========================================================

    momentum15 = _momentum(
        ind15,
        direction
    )

    score += momentum15

    if momentum15:
        reasons.append(
            "15M momentum confirmation"
        )

    # ========================================================
    # 5M SETUP
    # ========================================================

    structure_score5, structure_reasons5 = (
        _structure_score(
            struct5,
            direction
        )
    )

    score += structure_score5

    reasons.extend(
        [
            f"5M {x}"
            for x in structure_reasons5
        ]
    )

    momentum5 = _momentum(
        ind5,
        direction
    )

    score += momentum5

    if momentum5:
        reasons.append(
            "5M momentum confirmation"
        )

    # ========================================================
    # 5M DIRECTION CHECK
    # ========================================================

    trend5 = _trend(
        ind5
    )

    if direction == "LONG":

        if trend5 == "BULLISH":

            score += 2

            reasons.append(
                "5M trend aligned"
            )

        elif trend5 == "BEARISH":

            return _wait(
                symbol,
                score,
                reasons + [
                    "5M trend 15M yönüne ters"
                ]
            )

    else:

        if trend5 == "BEARISH":

            score += 2

            reasons.append(
                "5M trend aligned"
            )

        elif trend5 == "BULLISH":

            return _wait(
                symbol,
                score,
                reasons + [
                    "5M trend 15M yönüne ters"
                ]
            )

    # ========================================================
    # 1M ENTRY TRIGGER
    # ========================================================

    trigger_score, trigger_reasons = (
        _entry_trigger(
            struct1,
            ind1,
            direction
        )
    )

    score += trigger_score

    reasons.extend(
        [
            f"1M {x}"
            for x in trigger_reasons
        ]
    )

    # --------------------------------------------------------
    # HARD ENTRY REQUIREMENT
    # --------------------------------------------------------

    if trigger_score < 3:

        return _wait(
            symbol,
            score,
            reasons + [
                "1M giriş tetikleyicisi yetersiz"
            ]
        )

    # ========================================================
    # FINAL SCORE
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

    trade = _trade_parameters(

        symbol,

        df1,

        ind1,

        struct1,

        direction,

    )

    if trade is None:

        return _wait(
            symbol,
            score,
            reasons + [
                "Geçerli SL/TP oluşturulamadı"
            ]
        )

    # ========================================================
    # CONFIDENCE
    # ========================================================

    confidence = min(
        95,
        45 + score * 3
    )

    if (
        trend15
        and trend5
        and (
            (
                direction == "LONG"
                and trend15 == "BULLISH"
                and trend5 == "BULLISH"
            )
            or
            (
                direction == "SHORT"
                and trend15 == "BEARISH"
                and trend5 == "BEARISH"
            )
        )
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
            "15M > 5M > 1M",

        "status":
            "PAPER_ONLY",

        "reasons":
            reasons,

    })

    return trade
