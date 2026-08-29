# ============================================================
# CRYPTO RESEARCH AGENT
# SCALPING STRATEGY ENGINE
# ============================================================

"""
SCALPING ENGINE

Zaman dilimi zinciri:

15M -> Setup / fırsat
5M  -> Structure confirmation
1M  -> Entry confirmation

Kullanılan yapılar:

- Market Structure
- BOS
- CHoCH
- MSB
- Liquidity Sweep
- FVG
- Order Block
- Mitigation
- Displacement
- RSI
- EMA
- Volume
- ATR
- Risk / Reward

Bu modül doğrudan Binance'e emir göndermez.

Görevi:
    Piyasadaki setup'ı değerlendirir
    ve işlem yapılabilecek bir sinyal üretir.

Emir gönderme işi execution katmanına bırakılır.
"""


# ============================================================
# CONFIGURATION
# ============================================================

MIN_SCORE = 7

MIN_RR = 1.8

MAX_RR = 6.0

MAX_DISTANCE_FROM_ENTRY = 0.015

RSI_LONG_MIN = 45

RSI_LONG_MAX = 72

RSI_SHORT_MIN = 28

RSI_SHORT_MAX = 55


# ============================================================
# SAFE HELPERS
# ============================================================

def get_value(data, key, default=None):

    if not isinstance(data, dict):
        return default

    return data.get(key, default)


def safe_float(value, default=None):

    try:
        return float(value)

    except (TypeError, ValueError):

        return default


def last_candle(candles):

    if not candles:
        return None

    return candles[-1]


def candle_close(candles):

    candle = last_candle(candles)

    if not candle:
        return None

    return safe_float(candle.get("close"))


# ============================================================
# STRUCTURE BIAS
# ============================================================

def get_bias(snapshot):

    if not snapshot:
        return "NEUTRAL"

    try:

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

    except Exception:
        pass

    return "NEUTRAL"


# ============================================================
# MSB DETECTION
# ============================================================

def has_msb(snapshot, direction):

    if not snapshot:
        return False

    msb = snapshot.get(
        "msb",
        []
    )

    wanted = (
        "MSB_BULLISH"
        if direction == "LONG"
        else "MSB_BEARISH"
    )

    for event in msb[-10:]:

        if event.get("type") == wanted:

            return True

    return False


# ============================================================
# LIQUIDITY SWEEP
# ============================================================

def has_liquidity_sweep(
    snapshot,
    direction
):

    if not snapshot:
        return False

    sweeps = snapshot.get(
        "liquidity_sweeps",
        []
    )

    wanted = (
        "BULLISH_SWEEP"
        if direction == "LONG"
        else "BEARISH_SWEEP"
    )

    for event in sweeps[-10:]:

        if event.get("type") == wanted:

            return True

    return False


# ============================================================
# DISPLACEMENT
# ============================================================

def has_displacement(
    snapshot,
    direction
):

    if not snapshot:
        return False

    displacement = snapshot.get(
        "displacement",
        []
    )

    wanted = (
        "BULLISH"
        if direction == "LONG"
        else "BEARISH"
    )

    for event in displacement[-5:]:

        if event.get("direction") == wanted:

            return True

    return False


# ============================================================
# FVG
# ============================================================

def find_active_fvg(
    snapshot,
    direction,
    price
):

    if not snapshot:
        return None

    fvgs = snapshot.get(
        "fvg",
        []
    )

    wanted = (
        "LONG"
        if direction == "LONG"
        else "SHORT"
    )

    candidates = []

    for fvg in fvgs:

        if fvg.get("direction") != wanted:
            continue

        if fvg.get("filled") is True:
            continue

        bottom = safe_float(
            fvg.get("bottom")
        )

        top = safe_float(
            fvg.get("top")
        )

        if bottom is None or top is None:
            continue

        if bottom <= price <= top:

            candidates.append(fvg)

    if candidates:

        return
