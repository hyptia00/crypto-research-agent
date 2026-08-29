# ============================================================
# CRYPTO RESEARCH AGENT
# SPOT STRATEGY ENGINE
# ============================================================

"""
SPOT STRATEGY

Spot piyasada yalnızca LONG / ALIM aranır.

Ana akış:

4H  -> büyük trend
1H  -> trend + yapı teyidi
15M -> setup / entry

Ana prensip:

"Çok düştü = AL" değildir.

Spot alım için tercihen:

- HTF trend uyumu
- Market Structure
- Liquidity Sweep
- MSB / BOS / CHoCH
- Displacement
- FVG
- Order Block
- Mitigation
- EMA
- RSI
- MACD
- Volume
- BTC regime
- Risk / Reward

birlikte değerlendirilir.

Bu modül gerçek emir göndermez.
"""


# ============================================================
# CONFIG
# ============================================================

MIN_SCORE = 7
STRONG_SCORE = 10

MIN_RR = 2.0

MAX_STOP_PERCENT = 0.12

RSI_MIN = 42
RSI_MAX = 70

# Aşırı düşüşten sonra otomatik dip satın alma engeli
MAX_RECENT_DROP_PERCENT = -25.0


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

def has_bullish_msb(snapshot):

    if not snapshot:
        return False

    events = snapshot.get(
        "msb",
        []
    )

    return any(
        event.get("type")
        == "MSB_BULLISH"
        for event in events[-10:]
    )


# ============================================================
# BOS
# ============================================================

def has_bullish_bos(snapshot):

    if not snapshot:
        return False

    events = snapshot.get(
        "breaks",
        []
    )

    return any(
        event.get("type")
        == "BOS_BULLISH"
        for event in events[-10:]
    )


# ============================================================
# LIQUIDITY SWEEP
# ============================================================

def has_bullish_sweep(snapshot):

    if not snapshot:
        return False

    events = snapshot.get(
        "liquidity_sweeps",
        []
    )

    return any(
        event.get("type")
        == "BULLISH_SWEEP"
        for event in events[-10:]
    )


# ============================================================
# DISPLACEMENT
# ============================================================

def has_bullish_displacement(snapshot):

    if not snapshot:
        return False

    events = snapshot.get(
        "displacement",
        []
    )

    return any(
        event.get("direction")
        == "BULLISH"
        for event in events[-5:]
    )


# ============================================================
# FVG
# ============================================================

def has_bullish_fvg(snapshot):

    if not snapshot:
        return False

    fvgs = snapshot.get(
        "fvg",
        []
    )

    for fvg in fvgs[-10:]:

        if fvg.get(
            "direction"
        ) != "LONG":

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

def has_bullish_order_block(snapshot):

    if not snapshot:
        return False

    blocks = snapshot.get(
        "order_blocks",
        []
    )

    for block in blocks[-10:]:

        if block.get(
            "direction"
        ) == "LONG":

            return True

    return False


# ============================================================
# EMA TREND
# ============================================================

def ema_trend_ok(
    indicators
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

    # Fiyat EMA20 üzerinde olmalı
    if price < ema20:
        return False

    # EMA20 > EMA50 tercihi
    if (
        ema50 is not None
        and ema20 < ema50
    ):

        return False

    # EMA50 > EMA200 tercihi
    if (
        ema50 is not None
        and ema200 is not None
        and ema50 < ema200
    ):

        return False

    return True


# ============================================================
# RSI
# ============================================================

def rsi_ok(
    indicators
):

    if not indicators:
        return True

    value = safe_float(
        indicators.get("rsi")
    )

    if value is None:
        return True

    return (
        RSI_MIN
        <= value
        <= RSI_MAX
    )


# ============================================================
# MACD
# ============================================================

def macd_ok(
    indicators
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

    return histogram > 0


# ============================================================
# VOLUME
# ============================================================

def volume_ok(
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
# RECENT PRICE PERFORMANCE
# ============================================================

def recent_change(
    candles,
    periods=20
):

    if not candles:
        return 0.0

    if len(candles) <= periods:
        return 0.0

    old_price = safe_float(
        candles[-periods - 1].get(
            "close"
        )
    )

    current_price = safe_float(
        candles[-1].get(
            "close"
        )
    )

    if (
        old_price is None
        or current_price is None
        or old_price <= 0
    ):

        return 0.0

    return (
        (current_price - old_price)
        / old_price
    ) * 100


# ============================================================
# FALLING KNIFE FILTER
# ============================================================

def falling_knife_filter(
    candles_4h,
    snapshot_4h,
    indicators_4h
):

    """
    Çok sert düşen coinlerde sırf ucuzladı diye
    spot alımı engeller.

    Fakat bullish reversal oluşmuşsa yeniden
    değerlendirilmesine izin verir.
    """

    change = recent_change(
        candles_4h,
        20
    )

    if change > MAX_RECENT_DROP_PERCENT:

        return True

    # Sert düşüş var.
    # Ancak bullish MSB varsa toparlanma işareti
    # kabul edilir.

    if has_bullish_msb(
        snapshot_4h
    ):

        return True

    return False


# ============================================================
# MARKET REGIME
# ============================================================

def btc_regime_ok(
    btc_regime
):

    """
    Spot için BTC rejimi daha önemlidir.

    BTC SHORT rejimindeyken
    agresif altcoin alımı istemiyoruz.
    """

    if btc_regime in (
        None,
        "NEUTRAL"
    ):

        return True

    if btc_regime == "LONG":

        return True

    # BTC SHORT ise sadece çok güçlü
    # reversal setup'larına daha sonra izin verilebilir.
    return False


# ============================================================
# ENTRY ZONE
# ============================================================

def find_entry_zone(
    snapshot,
    price
):

    """
    Öncelik:

    1. Bullish FVG
    2. Bullish Order Block
    3. Market
    """

    # --------------------------------------------------------
    # FVG
    # --------------------------------------------------------

    fvgs = snapshot.get(
        "fvg",
        []
    )

    for fvg in reversed(fvgs):

        if fvg.get(
            "direction"
        ) != "LONG":

            continue

        if fvg.get(
            "filled"
        ):

            continue

        low = safe_float(
            fvg.get("bottom")
        )

        high = safe_float(
            fvg.get("top")
        )

        if (
            low is not None
            and high is not None
        ):

            return {
                "type": "FVG",
                "low": low,
                "high": high,
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
        ) != "LONG":

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
    entry,
    atr
):

    candidates = []

    # --------------------------------------------------------
    # 15M SWING LOW
    # --------------------------------------------------------

    swings_15m = snapshot_15m.get(
        "last_swings",
        {}
    )

    last_low = swings_15m.get(
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

    # --------------------------------------------------------
    # 1H SWING LOW
    # --------------------------------------------------------

    swings_1h = snapshot_1h.get(
        "last_swings",
        {}
    )

    last_low_1h = swings_1h.get(
        "last_low"
    )

    if last_low_1h:

        value = safe_float(
            last_low_1h.get(
                "price"
            )
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

        candidates.append(
            entry - (
                atr * 1.5
            )
        )

    # --------------------------------------------------------
    # FINAL STOP
    # --------------------------------------------------------

    valid = [
        x for x in candidates
        if x < entry
    ]

    if valid:

        return min(valid)

    return entry * 0.97


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

    return {

        "tp1":
            entry + risk * 2,

        "tp2":
            entry + risk * 3,

        "rr1":
            2.0,

        "rr2":
            3.0,
    }


# ============================================================
# SPOT EVALUATION
# ============================================================

def evaluate_spot(
    symbol,
    data,
    indicators,
    structures,
    btc_regime
):

    score = 0
    reasons = []

    # ========================================================
    # REQUIRED DATA
    # ========================================================

    candles_4h = data.get(
        "4h",
        []
    )

    candles_1h = data.get(
        "1h",
        []
    )

    candles_15m = data.get(
        "15m",
        []
    )

    if not candles_4h:
        return None

    if not candles_1h:
        return None

    if not candles_15m:
        return None

    # ========================================================
    # SNAPSHOTS
    # ========================================================

    snapshot_4h = structures.get(
        "4h",
        {}
    )

    snapshot_1h = structures.get(
        "1h",
        {}
    )

    snapshot_15m = structures.get(
        "15m",
        {}
    )

    # ========================================================
    # 4H STRUCTURE
    # ========================================================

    bias_4h = get_bias(
        snapshot_4h
    )

    if bias_4h == "LONG":

        score += 3

        reasons.append(
            "4H bullish structure"
        )

    else:

        return None

    # ========================================================
    # 1H STRUCTURE
    # ========================================================

    bias_1h = get_bias(
        snapshot_1h
    )

    if bias_1h == "LONG":

        score += 2

        reasons.append(
            "1H bullish structure"
        )

    else:

        return None

    # ========================================================
    # 15M STRUCTURE
    # ========================================================

    bias_15m = get_bias(
        snapshot_15m
    )

    if bias_15m == "LONG":

        score += 2

        reasons.append(
            "15M bullish structure"
        )

    else:

        return None

    # ========================================================
    # BULLISH MSB
    # ========================================================

    if has_bullish_msb(
        snapshot_15m
    ):

        score += 3

        reasons.append(
            "15M bullish MSB"
        )

    # ========================================================
    # LIQUIDITY SWEEP
    # ========================================================

    if has_bullish_sweep(
        snapshot_15m
    ):

        score += 2

        reasons.append(
            "15M liquidity sweep"
        )

    # ========================================================
    # BOS
    # ========================================================

    if has_bullish_bos(
        snapshot_15m
    ):

        score += 1

        reasons.append(
            "15M bullish BOS"
        )

    # ========================================================
    # DISPLACEMENT
    # ========================================================

    if has_bullish_displacement(
        snapshot_15m
    ):

        score += 2

        reasons.append(
            "15M bullish displacement"
        )

    # ========================================================
    # FVG
    # ========================================================

    if has_bullish_fvg(
        snapshot_15m
    ):

        score += 1

        reasons.append(
            "Bullish FVG"
        )

    # ========================================================
    # ORDER BLOCK
    # ========================================================

    if has_bullish_order_block(
        snapshot_15m
    ):

        score += 1

        reasons.append(
            "Bullish Order Block"
        )

    # ========================================================
    # 4H EMA
    # ========================================================

    ind_4h = indicators.get(
        "4h",
        {}
    )

    if ema_trend_ok(
        ind_4h
    ):

        score += 2

        reasons.append(
            "4H EMA trend"
        )

    # ========================================================
    # 1H EMA
    # ========================================================

    ind_1h = indicators.get(
        "1h",
        {}
    )

    if ema_trend_ok(
        ind_1h
    ):

        score += 2

        reasons.append(
            "1H EMA trend"
        )

    # ========================================================
    # RSI
    # ========================================================

    if rsi_ok(
        ind_1h
    ):

        score += 1

        reasons.append(
            "1H RSI uygun"
        )

    # ========================================================
    # MACD
    # ========================================================

    if macd_ok(
        ind_1h
    ):

        score += 1

        reasons.append(
            "1H MACD bullish"
        )

    # ========================================================
    # VOLUME
    # ========================================================

    ind_15m = indicators.get(
        "15m",
        {}
    )

    if volume_ok(
        ind_15m
    ):

        score += 1

        reasons.append(
            "15M volume uygun"
        )

    # ========================================================
    # BTC REGIME
    # ========================================================

    if btc_regime_ok(
        btc_regime
    ):

        score += 1

        reasons.append(
            "BTC regime uygun"
        )

    else:

        # BTC tersken spot işlem istemiyoruz.
        return None

    # ========================================================
    # FALLING KNIFE
    # ========================================================

    if not falling_knife_filter(
        candles_4h,
        snapshot_4h,
        ind_4h
    ):

        return None

    # ========================================================
    # SCORE CHECK
    # ========================================================

    if score < MIN_SCORE:

        return None

    # ========================================================
    # ENTRY
    # ========================================================

    entry = safe_float(
        candles_15m[-1].get(
            "close"
        )
    )

    if entry is None:

        return None

    # ========================================================
    # STOP
    # ========================================================

    atr = safe_float(
        ind_15m.get(
            "atr"
        )
    )

    stop = calculate_stop(

        snapshot_15m,

        snapshot_1h,

        entry,

        atr,

    )

    if stop >= entry:

        return None

    # ========================================================
    # STOP DISTANCE
    # ========================================================

    stop_distance = (
        abs(entry - stop)
        / entry
    )

    if stop_distance > MAX_STOP_PERCENT:

        return None

    # ========================================================
    # TARGETS
    # ========================================================

    targets = calculate_targets(
        entry,
        stop
    )

    if not targets["tp2"]:

        return None

    # ========================================================
    # R/R
    # ========================================================

    risk = abs(
        entry - stop
    )

    reward = abs(
        targets["tp2"]
        - entry
    )

    if risk <= 0:

        return None

    rr = reward / risk

    if rr < MIN_RR:

        return None

    # ========================================================
    # CONFIDENCE
    # ========================================================

    confidence = min(
        99,
        int(
            45
            + score * 4
        )
    )

    if score >= STRONG_SCORE:

        confidence = min(
            99,
            confidence + 5
        )

    # ========================================================
    # RESULT
    # ========================================================

    return {

        "symbol":
            symbol,

        "strategy":
            "SPOT",

        "signal":
            "LONG",

        "score":
            score,

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

        "timeframe":
            "4H > 1H > 15M",

        "btc_regime":
            btc_regime,

        "reasons":
            reasons,

        "execution":
            "PAPER_ONLY",

    }


# ============================================================
# PUBLIC FUNCTION
# ============================================================

def analyze_spot(
    symbol,
    data,
    indicators,
    structures,
    btc_regime="NEUTRAL"
):

    """
    Agent tarafından çağrılan ana fonksiyon.
    """

    try:

        result = evaluate_spot(

            symbol,

            data,

            indicators,

            structures,

            btc_regime,

        )

        if result is None:

            return {

                "symbol":
                    symbol,

                "strategy":
                    "SPOT",

                "signal":
                    "WAIT",

                "score":
                    0,

                "reason":
                    "Yeterli Spot setup oluşmadı",

            }

        return result

    except Exception as e:

        return {

            "symbol":
                symbol,

            "strategy":
                "SPOT",

            "signal":
                "ERROR",

            "score":
                0,

            "reason":
                str(e),

        }


# ============================================================
# SUMMARY
# ============================================================

def spot_summary(
    result
):

    if not result:

        return "SPOT: WAIT"

    if result.get(
        "signal"
    ) != "LONG":

        return (

            f'{result.get("symbol")} '
            f'SPOT WAIT | '
            f'{result.get("reason", "")}'

        )

    return (

        f'{result["symbol"]} '
        f'SPOT LONG | '

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
        "SPOT STRATEGY ENGINE"
    )

    print("=" * 60)

    print()

    print(
        "4H -> 1H -> 15M"
    )

    print()

    print(
        "SPOT yalnızca LONG arar."
    )

    print()

    print(
        "Market Structure"
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
        "BTC Regime"
    )

    print(
        "Falling Knife Protection"
    )

    print(
        "Entry / SL / TP / R:R"
    )

    print()

    print(
        "Gerçek emir: KAPALI"
    )

    print(
        "SPOT ENGINE HAZIR"
    )

    print("=" * 60)
