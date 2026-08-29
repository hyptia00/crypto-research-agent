# ============================================================
# CRYPTO RESEARCH AGENT
# FUTURES STRATEGY ENGINE
# ============================================================

"""
FUTURES STRATEGY

Ana akış:

4H  -> büyük trend
1H  -> trend / yapı teyidi
15M -> setup
5M  -> giriş bölgesi / confirmation

Kullanılan yapı:

- Market Structure
- BOS
- CHoCH
- MSB
- Liquidity Sweep
- FVG
- Order Block
- Displacement
- EMA
- RSI
- MACD
- Volume
- ATR
- BTC Market Regime
- Risk / Reward

Bu modül emir göndermez.
Sadece işlem sinyali üretir.
"""


# ============================================================
# CONFIG
# ============================================================

MIN_SCORE = 7
STRONG_SCORE = 10

MIN_RR = 2.0

MAX_STOP_PERCENT = 0.06

RSI_LONG_MIN = 45
RSI_LONG_MAX = 72

RSI_SHORT_MIN = 28
RSI_SHORT_MAX = 55


# ============================================================
# HELPERS
# ============================================================

def safe_float(value, default=None):

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def get_bias(snapshot):

    if not snapshot:
        return "NEUTRAL"

    structure = snapshot.get(
        "structure",
        {}
    )

    bias = structure.get(
        "bias",
        "SIDEWAYS"
    )

    if bias in (
        "BULLISH",
        "WEAK_BULLISH"
    ):
        return "LONG"

    if bias in (
        "BEARISH",
        "WEAK_BEARISH"
    ):
        return "SHORT"

    return "NEUTRAL"


# ============================================================
# MSB
# ============================================================

def has_msb(snapshot, direction):

    if not snapshot:
        return False

    events = snapshot.get(
        "msb",
        []
    )

    wanted = (
        "MSB_BULLISH"
        if direction == "LONG"
        else "MSB_BEARISH"
    )

    return any(
        event.get("type") == wanted
        for event in events[-10:]
    )


# ============================================================
# BOS
# ============================================================

def has_bos(snapshot, direction):

    if not snapshot:
        return False

    events = snapshot.get(
        "breaks",
        []
    )

    wanted = (
        "BOS_BULLISH"
        if direction == "LONG"
        else "BOS_BEARISH"
    )

    return any(
        event.get("type") == wanted
        for event in events[-10:]
    )


# ============================================================
# LIQUIDITY SWEEP
# ============================================================

def has_sweep(snapshot, direction):

    if not snapshot:
        return False

    events = snapshot.get(
        "liquidity_sweeps",
        []
    )

    wanted = (
        "BULLISH_SWEEP"
        if direction == "LONG"
        else "BEARISH_SWEEP"
    )

    return any(
        event.get("type") == wanted
        for event in events[-10:]
    )


# ============================================================
# DISPLACEMENT
# ============================================================

def has_displacement(
    snapshot,
    direction
):

    if not snapshot:
        return False

    events = snapshot.get(
        "displacement",
        []
    )

    wanted = (
        "BULLISH"
        if direction == "LONG"
        else "BEARISH"
    )

    return any(
        event.get("direction") == wanted
        for event in events[-5:]
    )


# ============================================================
# FVG
# ============================================================

def has_fvg(snapshot, direction):

    if not snapshot:
        return False

    fvgs = snapshot.get(
        "fvg",
        []
    )

    wanted = (
        "LONG"
        if direction == "LONG"
        else "SHORT"
    )

    for fvg in fvgs[-10:]:

        if fvg.get(
            "direction"
        ) != wanted:
            continue

        if fvg.get(
            "filled"
        ):
            continue

        return True

    return False


# ============================================================
# ORDER BLOCK
# ============================================================

def has_order_block(
    snapshot,
    direction
):

    if not snapshot:
        return False

    blocks = snapshot.get(
        "order_blocks",
        []
    )

    wanted = (
        "LONG"
        if direction == "LONG"
        else "SHORT"
    )

    for block in blocks[-10:]:

        if block.get(
            "direction"
        ) == wanted:

            return True

    return False


# ============================================================
# INDICATOR TREND
# ============================================================

def indicator_trend(
    indicators,
    direction
):

    if not indicators:
        return False

    price = safe_float(
        indicators.get("price")
    )

    ema20 = safe_float(
        indicators.get("ema20")
    )

    ema50 = safe_float(
        indicators.get("ema50")
    )

    ema200 = safe_float(
        indicators.get("ema200")
    )

    if price is None:
        return False

    if ema20 is None:
        return False

    if direction == "LONG":

        if price < ema20:
            return False

        if ema50 is not None:
            if ema20 < ema50:
                return False

        if ema200 is not None:
            if ema50 is not None:
                if ema50 < ema200:
                    return False

        return True

    else:

        if price > ema20:
            return False

        if ema50 is not None:
            if ema20 > ema50:
                return False

        if ema200 is not None:
            if ema50 is not None:
                if ema50 > ema200:
                    return False

        return True


# ============================================================
# RSI
# ============================================================

def rsi_confirmation(
    indicators,
    direction
):

    if not indicators:
        return True

    rsi = safe_float(
        indicators.get("rsi")
    )

    if rsi is None:
        return True

    if direction == "LONG":

        return (
            RSI_LONG_MIN
            <= rsi
            <= RSI_LONG_MAX
        )

    return (
        RSI_SHORT_MIN
        <= rsi
        <= RSI_SHORT_MAX
    )


# ============================================================
# MACD
# ============================================================

def macd_confirmation(
    indicators,
    direction
):

    if not indicators:
        return True

    histogram = safe_float(
        indicators.get(
            "macd_histogram"
        )
    )

    if histogram is None:
        return True

    if direction == "LONG":
        return histogram > 0

    return histogram < 0


# ============================================================
# VOLUME
# ============================================================

def volume_confirmation(
    indicators
):

    if not indicators:
        return True

    volume_data = indicators.get(
        "volume",
        {}
    )

    if not isinstance(
        volume_data,
        dict
    ):
        return True

    ratio = safe_float(
        volume_data.get(
            "ratio"
        )
    )

    if ratio is None:
        return True

    return ratio >= 0.8


# ============================================================
# TIMEFRAME TREND
# ============================================================

def timeframe_confirmation(
    structures,
    direction
):

    score = 0

    # --------------------------------------------------------
    # 4H
    # --------------------------------------------------------

    bias_4h = get_bias(
        structures.get(
            "4h",
            {}
        )
    )

    if bias_4h == direction:
        score += 2

    # --------------------------------------------------------
    # 1H
    # --------------------------------------------------------

    bias_1h = get_bias(
        structures.get(
            "1h",
            {}
        )
    )

    if bias_1h == direction:
        score += 2

    # --------------------------------------------------------
    # 15M
    # --------------------------------------------------------

    bias_15m = get_bias(
        structures.get(
            "15m",
            {}
        )
    )

    if bias_15m == direction:
        score += 2

    return score


# ============================================================
# BTC REGIME FILTER
# ============================================================

def btc_regime_ok(
    btc_regime,
    direction
):

    if btc_regime in (
        None,
        "NEUTRAL"
    ):
        return True

    if btc_regime == direction:
        return True

    # BTC karşı yöndeyse işlem tamamen yasak değil.
    # Ancak daha yüksek skor gerektirir.
    return False


# ============================================================
# ENTRY ZONE
# ============================================================

def find_entry_zone(
    snapshot,
    direction,
    price
):

    # --------------------------------------------------------
    # FVG
    # --------------------------------------------------------

    fvgs = snapshot.get(
        "fvg",
        []
    )

    wanted = (
        "LONG"
        if direction == "LONG"
        else "SHORT"
    )

    for fvg in reversed(fvgs):

        if fvg.get(
            "direction"
        ) != wanted:
            continue

        if fvg.get(
            "filled"
        ):
            continue

        bottom = safe_float(
            fvg.get("bottom")
        )

        top = safe_float(
            fvg.get("top")
        )

        if (
            bottom is not None
            and top is not None
        ):

            return {
                "type": "FVG",
                "low": bottom,
                "high": top,
            }

    # --------------------------------------------------------
    # ORDER BLOCK
    # --------------------------------------------------------

    blocks = snapshot.get(
        "order_blocks",
        []
    )

    for block in reversed(blocks):

        if block.get(
            "direction"
        ) != wanted:
            continue

        low = safe_float(
            block.get("low")
        )

        high = safe_float(
            block.get("high")
        )

        if (
            low is not None
            and high is not None
        ):

            return {
                "type": "ORDER_BLOCK",
                "low": low,
                "high": high,
            }

    return {
        "type": "MARKET",
        "low": price,
        "high": price,
    }


# ============================================================
# STOP LOSS
# ============================================================

def calculate_stop(
    snapshot_15m,
    snapshot_1h,
    direction,
    entry,
    atr
):

    candidates = []

    # --------------------------------------------------------
    # 15M SWING
    # --------------------------------------------------------

    swings = snapshot_15m.get(
        "last_swings",
        {}
    )

    if direction == "LONG":

        last_low = swings.get(
            "last_low"
        )

        if last_low:

            value = safe_float(
                last_low.get(
                    "price"
                )
            )

            if value is not None:
                candidates.append(
                    value
                )

    else:

        last_high = swings.get(
            "last_high"
        )

        if last_high:

            value = safe_float(
                last_high.get(
                    "price"
                )
            )

            if value is not None:
                candidates.append(
                    value
                )

    # --------------------------------------------------------
    # 1H SWING
    # --------------------------------------------------------

    swings_1h = snapshot_1h.get(
        "last_swings",
        {}
    )

    if direction == "LONG":

        low = swings_1h.get(
            "last_low"
        )

        if low:

            value = safe_float(
                low.get("price")
            )

            if value is not None:
                candidates.append(
                    value
                )

    else:

        high = swings_1h.get(
            "last_high"
        )

        if high:

            value = safe_float(
                high.get("price")
            )

            if value is not None:
                candidates.append(
                    value
                )

    # --------------------------------------------------------
    # ATR
    # --------------------------------------------------------

    atr = safe_float(
        atr
    )

    if atr is not None:

        if direction == "LONG":

            candidates.append(
                entry - (
                    atr * 1.5
                )
            )

        else:

            candidates.append(
                entry + (
                    atr * 1.5
                )
            )

    # --------------------------------------------------------
    # FINAL STOP
    # --------------------------------------------------------

    if direction == "LONG":

        valid = [
            x for x in candidates
            if x < entry
        ]

        if valid:

            return min(valid)

        return entry * 0.98

    valid = [
        x for x in candidates
        if x > entry
    ]

    if valid:

        return max(valid)

    return entry * 1.02


# ============================================================
# TARGETS
# ============================================================

def calculate_targets(
    entry,
    stop
):

    risk = abs(
        entry - stop
    )

    if risk <= 0:

        return {
            "tp1": None,
            "tp2": None,
            "rr1": 0,
            "rr2": 0,
        }

    tp1 = (
        entry
        + risk * 2
    )

    tp2 = (
        entry
        + risk * 3
    )

    return {
        "tp1": tp1,
        "tp2": tp2,
        "rr1": 2.0,
        "rr2": 3.0,
    }


def calculate_targets_directional(
    entry,
    stop,
    direction
):

    risk = abs(
        entry - stop
    )

    if risk <= 0:
        return {
            "tp1": None,
            "tp2": None,
            "rr1": 0,
            "rr2": 0,
        }

    if direction == "LONG":

        tp1 = entry + (
            risk * 2
        )

        tp2 = entry + (
            risk * 3
        )

    else:

        tp1 = entry - (
            risk * 2
        )

        tp2 = entry - (
            risk * 3
        )

    return {
        "tp1": tp1,
        "tp2": tp2,
        "rr1": 2.0,
        "rr2": 3.0,
    }


# ============================================================
# SCORE
# ============================================================

def evaluate_direction(
    direction,
    data,
    indicators,
    structures,
    btc_regime
):

    score = 0
    reasons = []

    # ========================================================
    # 4H / 1H / 15M ALIGNMENT
    # ========================================================

    alignment = timeframe_confirmation(
        structures,
        direction
    )

    score += alignment

    if alignment >= 4:

        reasons.append(
            "HTF structure uyumlu"
        )

    # ========================================================
    # 15M STRUCTURE
    # ========================================================

    snapshot_15m = structures.get(
        "15m",
        {}
    )

    bias_15m = get_bias(
        snapshot_15m
    )

    if bias_15m == direction:

        score += 2

        reasons.append(
            "15M structure yönü uyumlu"
        )

    else:

        return {
            "valid": False,
            "score": 0,
            "reasons": [
                "15M structure uyumsuz"
            ],
        }

    # ========================================================
    # MSB
    # ========================================================

    if has_msb(
        snapshot_15m,
        direction
    ):

        score += 3

        reasons.append(
            "15M MSB"
        )

    # ========================================================
    # BOS
    # ========================================================

    if has_bos(
        snapshot_15m,
        direction
    ):

        score += 1

        reasons.append(
            "15M BOS"
        )

    # ========================================================
    # LIQUIDITY
    # ========================================================

    if has_sweep(
        snapshot_15m,
        direction
    ):

        score += 2

        reasons.append(
            "15M liquidity sweep"
        )

    # ========================================================
    # DISPLACEMENT
    # ========================================================

    if has_displacement(
        snapshot_15m,
        direction
    ):

        score += 2

        reasons.append(
            "15M displacement"
        )

    # ========================================================
    # FVG / OB
    # ========================================================

    has_zone = False

    if has_fvg(
        snapshot_15m,
        direction
    ):

        score += 1

        has_zone = True

        reasons.append(
            "15M FVG"
        )

    if has_order_block(
        snapshot_15m,
        direction
    ):

        score += 1

        has_zone = True

        reasons.append(
            "15M Order Block"
        )

    # ========================================================
    # 1H INDICATORS
    # ========================================================

    indicators_1h = indicators.get(
        "1h",
        {}
    )

    if indicator_trend(
        indicators_1h,
        direction
    ):

        score += 2

        reasons.append(
            "1H EMA trend uyumlu"
        )

    if rsi_confirmation(
        indicators_1h,
        direction
    ):

        score += 1

        reasons.append(
            "1H RSI uygun"
        )

    if macd_confirmation(
        indicators_1h,
        direction
    ):

        score += 1

        reasons.append(
            "1H MACD uygun"
        )

    # ========================================================
    # 15M INDICATORS
    # ========================================================

    indicators_15m = indicators.get(
        "15m",
        {}
    )

    if volume_confirmation(
        indicators_15m
    ):

        score += 1

        reasons.append(
            "15M hacim uygun"
        )

    # ========================================================
    # BTC FILTER
    # ========================================================

    btc_aligned = btc_regime_ok(
        btc_regime,
        direction
    )

    if btc_aligned:

        score += 1

        reasons.append(
            "BTC market regime uyumlu"
        )

    else:

        # Karşı BTC rejiminde
        # sinyal için ekstra kalite gerekir.

        if score < 10:

            return {
                "valid": False,
                "score": score,
                "reasons": [
                    "BTC rejimi ters yönde"
                ],
            }

        reasons.append(
            "BTC rejimi ters fakat setup güçlü"
        )

    # ========================================================
    # MINIMUM SCORE
    # ========================================================

    if score < MIN_SCORE:

        return {
            "valid": False,
            "score": score,
            "reasons": reasons,
        }

    # ========================================================
    # RESULT
    # ========================================================

    return {
        "valid": True,
        "score": score,
        "reasons": reasons,
        "has_zone": has_zone,
    }


# ============================================================
# FINAL FUTURES ANALYSIS
# ============================================================

def analyze_futures(
    symbol,
    data,
    indicators,
    structures,
    btc_regime="NEUTRAL"
):

    """
    Futures LONG / SHORT analiz motoru.
    """

    if not data:

        return {
            "symbol": symbol,
            "signal": "WAIT",
            "score": 0,
            "reason": "Veri yok",
        }

    candidates = []

    for direction in (
        "LONG",
        "SHORT"
    ):

        evaluation = evaluate_direction(

            direction,

            data,

            indicators,

            structures,

            btc_regime,

        )

        if not evaluation["valid"]:
            continue

        # ----------------------------------------------------
        # ENTRY PRICE
        # ----------------------------------------------------

        candles_5m = data.get(
            "5m",
            []
        )

        candles_15m = data.get(
            "15m",
            []
        )

        if candles_5m:

            entry = safe_float(
                candles_5m[-1].get(
                    "close"
                )
            )

        elif candles_15m:

            entry = safe_float(
                candles_15m[-1].get(
                    "close"
                )
            )

        else:

            continue

        if entry is None:
            continue

        # ----------------------------------------------------
        # ATR
        # ----------------------------------------------------

        ind_15m = indicators.get(
            "15m",
            {}
        )

        atr = safe_float(
            ind_15m.get("atr")
        )

        # ----------------------------------------------------
        # STOP
        # ----------------------------------------------------

        stop = calculate_stop(

            structures.get(
                "15m",
                {}
            ),

            structures.get(
                "1h",
                {}
            ),

            direction,

            entry,

            atr,

        )

        # ----------------------------------------------------
        # STOP DISTANCE
        # ----------------------------------------------------

        stop_distance = (
            abs(entry - stop)
            / entry
        )

        if stop_distance > MAX_STOP_PERCENT:

            continue

        # ----------------------------------------------------
        # TARGETS
        # ----------------------------------------------------

        targets = (
            calculate_targets_directional(

                entry,

                stop,

                direction

            )
        )

        if not targets["tp2"]:

            continue

        # ----------------------------------------------------
        # R/R
        # ----------------------------------------------------

        risk = abs(
            entry - stop
        )

        reward = abs(
            targets["tp2"]
            - entry
        )

        if risk <= 0:
            continue

        rr = reward / risk

        if rr < MIN_RR:
            continue

        # ----------------------------------------------------
        # CONFIDENCE
        # ----------------------------------------------------

        confidence = min(

            99,

            int(
                45
                + evaluation["score"] * 4
            )

        )

        if evaluation["score"] >= STRONG_SCORE:

            confidence = min(
                99,
                confidence + 5
            )

        # ----------------------------------------------------
        # SIGNAL
        # ----------------------------------------------------

        candidates.append({

            "symbol":
                symbol,

            "strategy":
                "FUTURES",

            "signal":
                direction,

            "score":
                evaluation["score"],

            "confidence":
                confidence,

            "entry":
                entry,

            "stop":
                stop,

            "tp1":
                targets["tp1"],

            "tp2":
                targets["tp2"],

            "rr":
                rr,

            "btc_regime":
                btc_regime,

            "timeframe":
                "4H > 1H > 15M > 5M",

            "reasons":
                evaluation["reasons"],

        })

    # ========================================================
    # NO SIGNAL
    # ========================================================

    if not candidates:

        return {

            "symbol":
                symbol,

            "strategy":
                "FUTURES",

            "signal":
                "WAIT",

            "score":
                0,

            "reason":
                "Yeterli Futures setup oluşmadı",

        }

    # ========================================================
    # BEST
    # ========================================================

    candidates.sort(

        key=lambda x:
        (
            x["score"],
            x["rr"],
            x["confidence"],
        ),

        reverse=True

    )

    return candidates[0]


# ============================================================
# SUMMARY
# ============================================================

def futures_summary(
    result
):

    if not result:
        return "FUTURES: WAIT"

    if result.get(
        "signal"
    ) == "WAIT":

        return (
            f'{result.get("symbol")} '
            f'FUTURES WAIT | '
            f'{result.get("reason", "")}'
        )

    return (

        f'{result["symbol"]} '
        f'{result["signal"]} | '

        f'Skor: '
        f'{result["score"]} | '

        f'Güven: '
        f'%{result["confidence"]} | '

        f'Entry: '
        f'{result["entry"]} | '

        f'SL: '
        f'{result["stop"]} | '

        f'TP1: '
        f'{result["tp1"]} | '

        f'TP2: '
        f'{result["tp2"]} | '

        f'R/R: '
        f'{result["rr"]:.2f}'

    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)

    print(
        "FUTURES STRATEGY ENGINE"
    )

    print("=" * 60)

    print()

    print(
        "4H -> 1H -> 15M -> 5M"
    )

    print()

    print(
        "LONG / SHORT"
    )

    print(
        "MSB / BOS / CHoCH"
    )

    print(
        "Liquidity Sweep"
    )

    print(
        "FVG / Order Block"
    )

    print(
        "Displacement"
    )

    print(
        "EMA / RSI / MACD / Volume"
    )

    print(
        "BTC Regime Filter"
    )

    print(
        "Entry / SL / TP / R:R"
    )

    print()

    print(
        "Gerçek emir: KAPALI"
    )

    print(
        "FUTURES ENGINE HAZIR"
    )

    print("=" * 60)
