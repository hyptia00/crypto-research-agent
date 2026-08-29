# ============================================================
# MARKET STRUCTURE ENGINE
# ============================================================

import pandas as pd


def _find_swings(df, window=2):

    highs = []
    lows = []

    if df is None or len(df) < (window * 2 + 1):
        return highs, lows

    high_values = df["high"].astype(float).values
    low_values = df["low"].astype(float).values

    for i in range(window, len(df) - window):

        left_high = high_values[
            i - window:i
        ]

        right_high = high_values[
            i + 1:i + window + 1
        ]

        left_low = low_values[
            i - window:i
        ]

        right_low = low_values[
            i + 1:i + window + 1
        ]

        if (
            high_values[i] > max(left_high)
            and high_values[i] > max(right_high)
        ):
            highs.append({
                "index": i,
                "price": float(high_values[i])
            })

        if (
            low_values[i] < min(left_low)
            and low_values[i] < min(right_low)
        ):
            lows.append({
                "index": i,
                "price": float(low_values[i])
            })

    return highs, lows


def analyze_structure(df):

    if df is None:
        return {
            "trend": "UNKNOWN",
            "structure": "UNKNOWN",
            "bos": False,
            "choch": False,
            "swing_high": None,
            "swing_low": None,
        }

    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)

    required = [
        "high",
        "low",
        "close",
    ]

    for column in required:

        if column not in df.columns:

            return {
                "trend": "UNKNOWN",
                "structure": "UNKNOWN",
                "bos": False,
                "choch": False,
                "swing_high": None,
                "swing_low": None,
            }

    if len(df) < 10:

        return {
            "trend": "UNKNOWN",
            "structure": "INSUFFICIENT_DATA",
            "bos": False,
            "choch": False,
            "swing_high": None,
            "swing_low": None,
        }

    highs, lows = _find_swings(
        df,
        window=2
    )

    last_close = float(
        df["close"].iloc[-1]
    )

    # --------------------------------------------------------
    # DEFAULT
    # --------------------------------------------------------

    trend = "SIDEWAYS"
    structure = "RANGE"

    bos = False
    choch = False

    # --------------------------------------------------------
    # SWING LEVELS
    # --------------------------------------------------------

    swing_high = (
        highs[-1]["price"]
        if highs
        else None
    )

    swing_low = (
        lows[-1]["price"]
        if lows
        else None
    )

    # --------------------------------------------------------
    # HIGHER HIGH / HIGHER LOW
    # --------------------------------------------------------

    higher_high = False
    higher_low = False

    lower_high = False
    lower_low = False

    if len(highs) >= 2:

        higher_high = (
            highs[-1]["price"]
            > highs[-2]["price"]
        )

        lower_high = (
            highs[-1]["price"]
            < highs[-2]["price"]
        )

    if len(lows) >= 2:

        higher_low = (
            lows[-1]["price"]
            > lows[-2]["price"]
        )

        lower_low = (
            lows[-1]["price"]
            < lows[-2]["price"]
        )

    # --------------------------------------------------------
    # TREND
    # --------------------------------------------------------

    if higher_high and higher_low:

        trend = "UP"
        structure = "HH_HL"

    elif lower_high and lower_low:

        trend = "DOWN"
        structure = "LH_LL"

    else:

        trend = "SIDEWAYS"
        structure = "RANGE"

    # --------------------------------------------------------
    # BREAK OF STRUCTURE
    # --------------------------------------------------------

    if (
        swing_high is not None
        and last_close > swing_high
    ):

        bos = True

    if (
        swing_low is not None
        and last_close < swing_low
    ):

        bos = True

    # --------------------------------------------------------
    # CHoCH
    # --------------------------------------------------------

    if (
        trend == "UP"
        and lower_low
    ):

        choch = True

    elif (
        trend == "DOWN"
        and higher_high
    ):

        choch = True

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    return {

        "trend":
            trend,

        "structure":
            structure,

        "bos":
            bos,

        "choch":
            choch,

        "swing_high":
            swing_high,

        "swing_low":
            swing_low,

        "higher_high":
            higher_high,

        "higher_low":
            higher_low,

        "lower_high":
            lower_high,

        "lower_low":
            lower_low,

        "last_close":
            last_close,

    }
