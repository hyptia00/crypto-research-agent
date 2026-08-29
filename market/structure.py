# ============================================================
# MARKET STRUCTURE ENGINE
# ============================================================

import pandas as pd


# ============================================================
# HELPERS
# ============================================================

def _prepare(df):

    if df is None:
        return pd.DataFrame()

    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)

    required = [
        "high",
        "low",
        "close",
    ]

    for column in required:

        if column not in df.columns:
            return pd.DataFrame()

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    return df.dropna(
        subset=required
    ).copy()


# ============================================================
# SWINGS
# ============================================================

def find_swings(
    df,
    window=2,
):

    df = _prepare(df)

    highs = []
    lows = []

    if len(df) < (
        window * 2 + 1
    ):
        return highs, lows

    for i in range(
        window,
        len(df) - window
    ):

        high = float(
            df["high"].iloc[i]
        )

        low = float(
            df["low"].iloc[i]
        )

        left_high = df[
            "high"
        ].iloc[
            i - window:i
        ]

        right_high = df[
            "high"
        ].iloc[
            i + 1:i + window + 1
        ]

        left_low = df[
            "low"
        ].iloc[
            i - window:i
        ]

        right_low = df[
            "low"
        ].iloc[
            i + 1:i + window + 1
        ]

        if (
            high > left_high.max()
            and high > right_high.max()
        ):

            highs.append({
                "index": i,
                "price": high,
            })

        if (
            low < left_low.min()
            and low < right_low.min()
        ):

            lows.append({
                "index": i,
                "price": low,
            })

    return highs, lows


# ============================================================
# TREND
# ============================================================

def detect_trend(
    highs,
    lows,
):

    if (
        len(highs) < 2
        or len(lows) < 2
    ):

        return "UNKNOWN"

    hh = (
        highs[-1]["price"]
        >
        highs[-2]["price"]
    )

    hl = (
        lows[-1]["price"]
        >
        lows[-2]["price"]
    )

    lh = (
        highs[-1]["price"]
        <
        highs[-2]["price"]
    )

    ll = (
        lows[-1]["price"]
        <
        lows[-2]["price"]
    )

    if hh and hl:
        return "BULLISH"

    if lh and ll:
        return "BEARISH"

    return "SIDEWAYS"


# ============================================================
# BOS / MSB
# ============================================================

def detect_breaks(
    df,
    highs,
    lows,
):

    if len(df) == 0:
        return {}

    close = float(
        df["close"].iloc[-1]
    )

    result = {

        "bullish_bos": False,
        "bearish_bos": False,

        "bullish_msb": False,
        "bearish_msb": False,

        "broken_high": None,
        "broken_low": None,
    }

    if highs:

        previous_high = highs[-1][
            "price"
        ]

        result[
            "broken_high"
        ] = previous_high

        if close > previous_high:

            result[
                "bullish_bos"
            ] = True

            result[
                "bullish_msb"
            ] = True

    if lows:

        previous_low = lows[-1][
            "price"
        ]

        result[
            "broken_low"
        ] = previous_low

        if close < previous_low:

            result[
                "bearish_bos"
            ] = True

            result[
                "bearish_msb"
            ] = True

    return result


# ============================================================
# CHoCH
# ============================================================

def detect_choch(
    trend,
    breaks,
):

    bullish = False
    bearish = False

    if trend == "BEARISH":

        if breaks.get(
            "bullish_bos"
        ):

            bullish = True

    if trend == "BULLISH":

        if breaks.get(
            "bearish_bos"
        ):

            bearish = True

    return {

        "bullish_choch":
            bullish,

        "bearish_choch":
            bearish,
    }


# ============================================================
# LIQUIDITY SWEEP
# ============================================================

def detect_liquidity_sweep(
    df,
    highs,
    lows,
):

    if len(df) < 2:
        return {}

    current_high = float(
        df["high"].iloc[-1]
    )

    current_low = float(
        df["low"].iloc[-1]
    )

    current_close = float(
        df["close"].iloc[-1]
    )

    result = {

        "bullish_sweep": False,
        "bearish_sweep": False,

        "swept_high": None,
        "swept_low": None,
    }

    # --------------------------------------------------------
    # SELL-SIDE LIQUIDITY SWEEP
    # Wick below previous swing low,
    # close back above it.
    # --------------------------------------------------------

    if lows:

        low = lows[-1]["price"]

        if (
            current_low < low
            and current_close > low
        ):

            result[
                "bullish_sweep"
            ] = True

            result[
                "swept_low"
            ] = low

    # --------------------------------------------------------
    # BUY-SIDE LIQUIDITY SWEEP
    # Wick above previous swing high,
    # close back below it.
    # --------------------------------------------------------

    if highs:

        high = highs[-1]["price"]

        if (
            current_high > high
            and current_close < high
        ):

            result[
                "bearish_sweep"
            ] = True

            result[
                "swept_high"
            ] = high

    return result


# ============================================================
# FAIR VALUE GAP
# ============================================================

def detect_fvg(
    df,
):

    df = _prepare(df)

    if len(df) < 3:

        return []

    fvgs = []

    for i in range(
        2,
        len(df)
    ):

        candle_1_high = float(
            df["high"].iloc[i - 2]
        )

        candle_1_low = float(
            df["low"].iloc[i - 2]
        )

        candle_3_high = float(
            df["high"].iloc[i]
        )

        candle_3_low = float(
            df["low"].iloc[i]
        )

        # ----------------------------------------------------
        # BULLISH FVG
        # ----------------------------------------------------

        if candle_3_low > candle_1_high:

            fvgs.append({

                "type":
                    "BULLISH",

                "index":
                    i,

                "low":
                    candle_1_high,

                "high":
                    candle_3_low,

                "size":
                    candle_3_low
                    - candle_1_high,
            })

        # ----------------------------------------------------
        # BEARISH FVG
        # ----------------------------------------------------

        elif candle_3_high < candle_1_low:

            fvgs.append({

                "type":
                    "BEARISH",

                "index":
                    i,

                "low":
                    candle_3_high,

                "high":
                    candle_1_low,

                "size":
                    candle_1_low
                    - candle_3_high,
            })

    return fvgs


# ============================================================
# COMPLETE ANALYSIS
# ============================================================

def analyze_structure(
    df,
):

    df = _prepare(df)

    if len(df) < 20:

        return {

            "trend":
                "UNKNOWN",

            "structure":
                "INSUFFICIENT_DATA",

            "bos":
                False,

            "choch":
                False,

            "msb":
                False,

            "liquidity_sweep":
                False,

            "fvg":
                None,

        }

    highs, lows = find_swings(
        df,
        window=2
    )

    trend = detect_trend(
        highs,
        lows
    )

    breaks = detect_breaks(
        df,
        highs,
        lows
    )

    choch = detect_choch(
        trend,
        breaks
    )

    sweep = detect_liquidity_sweep(
        df,
        highs,
        lows
    )

    fvgs = detect_fvg(
        df
    )

    # --------------------------------------------------------
    # STRUCTURE LABEL
    # --------------------------------------------------------

    if trend == "BULLISH":

        structure = "HH_HL"

    elif trend == "BEARISH":

        structure = "LH_LL"

    else:

        structure = "RANGE"

    # --------------------------------------------------------
    # LAST FVG
    # --------------------------------------------------------

    last_fvg = (
        fvgs[-1]
        if fvgs
        else None
    )

    # --------------------------------------------------------
    # COMBINED EVENTS
    # --------------------------------------------------------

    bullish_bos = breaks[
        "bullish_bos"
    ]

    bearish_bos = breaks[
        "bearish_bos"
    ]

    bullish_msb = breaks[
        "bullish_msb"
    ]

    bearish_msb = breaks[
        "bearish_msb"
    ]

    bullish_choch = choch[
        "bullish_choch"
    ]

    bearish_choch = choch[
        "bearish_choch"
    ]

    bullish_sweep = sweep[
        "bullish_sweep"
    ]

    bearish_sweep = sweep[
        "bearish_sweep"
    ]

    return {

        # ----------------------------------------------------
        # BASIC
        # ----------------------------------------------------

        "trend":
            trend,

        "structure":
            structure,

        # ----------------------------------------------------
        # BOS
        # ----------------------------------------------------

        "bos":
            (
                bullish_bos
                or
                bearish_bos
            ),

        "bullish_bos":
            bullish_bos,

        "bearish_bos":
            bearish_bos,

        # ----------------------------------------------------
        # MSB
        # ----------------------------------------------------

        "msb":
            (
                bullish_msb
                or
                bearish_msb
            ),

        "bullish_msb":
            bullish_msb,

        "bearish_msb":
            bearish_msb,

        # ----------------------------------------------------
        # CHoCH
        # ----------------------------------------------------

        "choch":
            (
                bullish_choch
                or
                bearish_choch
            ),

        "bullish_choch":
            bullish_choch,

        "bearish_choch":
            bearish_choch,

        # ----------------------------------------------------
        # LIQUIDITY
        # ----------------------------------------------------

        "liquidity_sweep":
            (
                bullish_sweep
                or
                bearish_sweep
            ),

        "bullish_sweep":
            bullish_sweep,

        "bearish_sweep":
            bearish_sweep,

        "swept_high":
            sweep.get(
                "swept_high"
            ),

        "swept_low":
            sweep.get(
                "swept_low"
            ),

        # ----------------------------------------------------
        # FVG
        # ----------------------------------------------------

        "fvg":
            last_fvg,

        "fvgs":
            fvgs,

        # ----------------------------------------------------
        # SWINGS
        # ----------------------------------------------------

        "swing_high":
            (
                highs[-1]["price"]
                if highs
                else None
            ),

        "swing_low":
            (
                lows[-1]["price"]
                if lows
                else None
            ),

        "swing_highs":
            highs,

        "swing_lows":
            lows,

        }
