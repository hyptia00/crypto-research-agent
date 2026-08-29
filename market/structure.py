# ============================================================
# CRYPTO RESEARCH AGENT
# MARKET STRUCTURE ENGINE
# ============================================================

"""
Market Structure Engine

Tespit edilen yapılar:

- Swing High
- Swing Low
- BOS  (Break of Structure)
- CHoCH (Change of Character)
- MSB  (Market Structure Break)
- Liquidity Sweep
- Fair Value Gap (FVG)
- Order Block
- Mitigation
- Premium / Discount
- Structure Bias

Bu modül doğrudan işlem açmaz.
Sadece piyasa yapısını analiz eder.

Strategy motoru bu verileri kullanarak
LONG / SHORT / WAIT kararı verecektir.
"""


# ============================================================
# BASIC HELPERS
# ============================================================

def _float(value):
    return float(value)


def _high(candle):
    return _float(candle["high"])


def _low(candle):
    return _float(candle["low"])


def _open(candle):
    return _float(candle["open"])


def _close(candle):
    return _float(candle["close"])


def _volume(candle):
    return _float(candle.get("volume", 0))


# ============================================================
# SWING DETECTION
# ============================================================

def find_swings(candles, left=2, right=2):
    """
    Swing High / Swing Low tespiti.

    Bir mumun solundaki ve sağındaki belirli sayıdaki
    mumdan daha yüksek/düşük olması swing kabul edilir.

    Örnek:

        Swing High

             H
             |
        -----|-----
          /     \

    """

    if len(candles) < left + right + 1:
        return []

    swings = []

    for i in range(left, len(candles) - right):

        current_high = _high(candles[i])
        current_low = _low(candles[i])

        left_highs = [
            _high(candles[j])
            for j in range(i - left, i)
        ]

        right_highs = [
            _high(candles[j])
            for j in range(i + 1, i + right + 1)
        ]

        left_lows = [
            _low(candles[j])
            for j in range(i - left, i)
        ]

        right_lows = [
            _low(candles[j])
            for j in range(i + 1, i + right + 1)
        ]

        is_swing_high = (
            current_high > max(left_highs)
            and current_high >= max(right_highs)
        )

        is_swing_low = (
            current_low < min(left_lows)
            and current_low <= min(right_lows)
        )

        if is_swing_high:

            swings.append({
                "index": i,
                "type": "HIGH",
                "price": current_high,
            })

        if is_swing_low:

            swings.append({
                "index": i,
                "type": "LOW",
                "price": current_low,
            })

    return swings


# ============================================================
# LAST SWINGS
# ============================================================

def get_last_swings(swings):
    """
    En son swing high ve swing low değerlerini döndürür.
    """

    highs = [
        x for x in swings
        if x["type"] == "HIGH"
    ]

    lows = [
        x for x in swings
        if x["type"] == "LOW"
    ]

    return {
        "last_high": highs[-1] if highs else None,
        "previous_high": highs[-2] if len(highs) >= 2 else None,

        "last_low": lows[-1] if lows else None,
        "previous_low": lows[-2] if len(lows) >= 2 else None,
    }


# ============================================================
# MARKET STRUCTURE
# ============================================================

def determine_structure(swings):
    """
    Swing dizisinden genel piyasa yapısını belirler.

    HH + HL  = Bullish
    LH + LL  = Bearish
    Karışık  = Sideways
    """

    highs = [
        x for x in swings
        if x["type"] == "HIGH"
    ]

    lows = [
        x for x in swings
        if x["type"] == "LOW"
    ]

    bullish = 0
    bearish = 0

    if len(highs) >= 2:

        if highs[-1]["price"] > highs[-2]["price"]:
            bullish += 1

        elif highs[-1]["price"] < highs[-2]["price"]:
            bearish += 1

    if len(lows) >= 2:

        if lows[-1]["price"] > lows[-2]["price"]:
            bullish += 1

        elif lows[-1]["price"] < lows[-2]["price"]:
            bearish += 1

    if bullish >= 2:
        bias = "BULLISH"

    elif bearish >= 2:
        bias = "BEARISH"

    elif bullish > bearish:
        bias = "WEAK_BULLISH"

    elif bearish > bullish:
        bias = "WEAK_BEARISH"

    else:
        bias = "SIDEWAYS"

    return {
        "bias": bias,
        "bullish_points": bullish,
        "bearish_points": bearish,
    }


# ============================================================
# BOS / CHOCH
# ============================================================

def detect_structure_breaks(candles, swings):
    """
    BOS ve CHoCH tespiti.

    BOS:
        Mevcut trend yönünde önemli swing kırılması.

    CHoCH:
        Mevcut trendin tersine ilk anlamlı yapı kırılması.

    MSB:
        Burada daha güçlü structure reversal olarak
        ayrıca işaretlenir.
    """

    if not candles or not swings:
        return []

    events = []

    structure = determine_structure(swings)

    current_bias = structure["bias"]

    for swing in swings:

        index = swing["index"]
        price = swing["price"]

        # Swing'den sonraki mumları kontrol et
        for i in range(index + 1, len(candles)):

            close = _close(candles[i])
            high = _high(candles[i])
            low = _low(candles[i])

            # ------------------------------------------------
            # HIGH BREAK
            # ------------------------------------------------

            if swing["type"] == "HIGH":

                if close > price:

                    if current_bias in (
                        "BULLISH",
                        "WEAK_BULLISH"
                    ):

                        event_type = "BOS_BULLISH"

                    else:

                        event_type = "CHOCH_BULLISH"

                    events.append({
                        "index": i,
                        "type": event_type,
                        "direction": "BULLISH",
                        "broken_level": price,
                        "break_price": close,
                        "swing_index": index,
                    })

                    break

            # ------------------------------------------------
            # LOW BREAK
            # ------------------------------------------------

            if swing["type"] == "LOW":

                if close < price:

                    if current_bias in (
                        "BEARISH",
                        "WEAK_BEARISH"
                    ):

                        event_type = "BOS_BEARISH"

                    else:

                        event_type = "CHOCH_BEARISH"

                    events.append({
                        "index": i,
                        "type": event_type,
                        "direction": "BEARISH",
                        "broken_level": price,
                        "break_price": close,
                        "swing_index": index,
                    })

                    break

    return _remove_duplicate_events(events)


def _remove_duplicate_events(events):

    result = []

    seen = set()

    for event in events:

        key = (
            event["index"],
            event["type"],
            round(event["broken_level"], 10)
        )

        if key in seen:
            continue

        seen.add(key)

        result.append(event)

    return result


# ============================================================
# MSB
# ============================================================

def detect_msb(candles, swings):
    """
    Market Structure Break.

    Güçlü yön değişimi için daha seçici filtre.

    Bullish MSB:

        önce bearish yapı
        +
        önemli swing high kırılımı
        +
        kapanışın kırılan seviyenin üzerinde olması

    Bearish MSB:

        önce bullish yapı
        +
        önemli swing low kırılımı
        +
        kapanışın kırılan seviyenin altında olması
    """

    breaks = detect_structure_breaks(
        candles,
        swings
    )

    structure = determine_structure(
        swings
    )

    events = []

    for event in breaks:

        if event["type"] == "CHOCH_BULLISH":

            events.append({
                **event,
                "type": "MSB_BULLISH",
                "strength": "STRONG",
            })

        elif event["type"] == "CHOCH_BEARISH":

            events.append({
                **event,
                "type": "MSB_BEARISH",
                "strength": "STRONG",
            })

    return events


# ============================================================
# LIQUIDITY SWEEP
# ============================================================

def detect_liquidity_sweeps(
    candles,
    swings,
    tolerance=0.001
):
    """
    Liquidity Sweep:

    Bullish sweep:
        fiyat önce eski low'un altına iner
        sonra tekrar üstüne kapanır.

    Bearish sweep:
        fiyat eski high'ın üstüne çıkar
        sonra tekrar altına kapanır.

    Bu özellikle 15M scalping taramasında önemlidir.
    """

    events = []

    highs = [
        x for x in swings
        if x["type"] == "HIGH"
    ]

    lows = [
        x for x in swings
        if x["type"] == "LOW"
    ]

    for swing in highs:

        level = swing["price"]

        for i in range(
            swing["index"] + 1,
            len(candles)
        ):

            high = _high(candles[i])
            close = _close(candles[i])

            if high > level:

                distance = (
                    high - level
                ) / level

                if distance >= tolerance:

                    if close < level:

                        events.append({
                            "index": i,
                            "type": "BEARISH_SWEEP",
                            "level": level,
                            "sweep_price": high,
                            "close": close,
                            "direction": "SHORT",
                        })

                        break

    for swing in lows:

        level = swing["price"]

        for i in range(
            swing["index"] + 1,
            len(candles)
        ):

            low = _low(candles[i])
            close = _close(candles[i])

            if low < level:

                distance = (
                    level - low
                ) / level

                if distance >= tolerance:

                    if close > level:

                        events.append({
                            "index": i,
                            "type": "BULLISH_SWEEP",
                            "level": level,
                            "sweep_price": low,
                            "close": close,
                            "direction": "LONG",
                        })

                        break

    return events


# ============================================================
# FAIR VALUE GAP
# ============================================================

def detect_fvg(candles):
    """
    3-candle Fair Value Gap.

    Bullish FVG:

        candle 1 high < candle 3 low

    Bearish FVG:

        candle 1 low > candle 3 high
    """

    if len(candles) < 3:
        return []

    gaps = []

    for i in range(2, len(candles)):

        first = candles[i - 2]
        middle = candles[i - 1]
        third = candles[i]

        first_high = _high(first)
        first_low = _low(first)

        third_high = _high(third)
        third_low = _low(third)

        # ----------------------------------------------
        # BULLISH FVG
        # ----------------------------------------------

        if third_low > first_high:

            gaps.append({
                "index": i,
                "type": "BULLISH_FVG",
                "direction": "LONG",
                "bottom": first_high,
                "top": third_low,
                "size": third_low - first_high,
                "filled": False,
            })

        # ----------------------------------------------
        # BEARISH FVG
        # ----------------------------------------------

        elif third_high < first_low:

            gaps.append({
                "index": i,
                "type": "BEARISH_FVG",
                "direction": "SHORT",
                "bottom": third_high,
                "top": first_low,
                "size": first_low - third_high,
                "filled": False,
            })

    return gaps


# ============================================================
# FVG MITIGATION
# ============================================================

def update_fvg_mitigation(
    candles,
    gaps
):
    """
    FVG'nin sonradan doldurulup doldurulmadığını kontrol eder.
    """

    updated = []

    for gap in gaps:

        gap = dict(gap)

        start = gap["index"] + 1

        for i in range(
            start,
            len(candles)
        ):

            high = _high(candles[i])
            low = _low(candles[i])

            if gap["direction"] == "LONG":

                if low <= gap["bottom"]:

                    gap["filled"] = True
                    gap["filled_index"] = i
                    break

            else:

                if high >= gap["top"]:

                    gap["filled"] = True
                    gap["filled_index"] = i
                    break

        updated.append(gap)

    return updated


# ============================================================
# ORDER BLOCK
# ============================================================

def detect_order_blocks(
    candles,
    swings
):
    """
    Basit Order Block tespiti.

    Bullish OB:
        önemli bullish displacement öncesindeki
        son bearish candle.

    Bearish OB:
        önemli bearish displacement öncesindeki
        son bullish candle.

    Not:
    OB tek başına işlem sinyali değildir.
    Structure + displacement + mitigation
    ile kullanılacaktır.
    """

    if len(candles) < 3:
        return []

    blocks = []

    for i in range(1, len(candles)):

        previous = candles[i - 1]
        current = candles[i]

        prev_open = _open(previous)
        prev_close = _close(previous)

        current_open = _open(current)
        current_close = _close(current)

        current_high = _high(current)
        current_low = _low(current)

        previous_high = _high(previous)
        previous_low = _low(previous)

        # ------------------------------------------------
        # BULLISH DISPLACEMENT
        # ------------------------------------------------

        bullish_displacement = (
            current_close > current_open
            and current_close > previous_high
        )

        if bullish_displacement:

            if prev_close < prev_open:

                blocks.append({
                    "index": i - 1,
                    "type": "BULLISH_OB",
                    "direction": "LONG",
                    "high": prev_open,
                    "low": prev_close,
                    "open": prev_open,
                    "close": prev_close,
                    "mitigated": False,
                })

        # ------------------------------------------------
        # BEARISH DISPLACEMENT
        # ------------------------------------------------

        bearish_displacement = (
            current_close < current_open
            and current_close < previous_low
        )

        if bearish_displacement:

            if prev_close > prev_open:

                blocks.append({
                    "index": i - 1,
                    "type": "BEARISH_OB",
                    "direction": "SHORT",
                    "high": prev_close,
                    "low": prev_open,
                    "open": prev_open,
