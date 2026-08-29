# ============================================================
# CRYPTO RESEARCH AGENT
# TECHNICAL INDICATORS
# ============================================================

import pandas as pd
import numpy as np


# ------------------------------------------------------------
# EMA
# ------------------------------------------------------------

def ema(series, period):
    return series.ewm(
        span=period,
        adjust=False
    ).mean()


def add_ema(df, fast=20, slow=50):
    df = df.copy()

    df["ema20"] = ema(
        df["close"],
        fast
    )

    df["ema50"] = ema(
        df["close"],
        slow
    )

    return df


# ------------------------------------------------------------
# RSI
# ------------------------------------------------------------

def rsi(series, period=14):
    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period
    ).mean()

    rs = avg_gain / avg_loss.replace(
        0,
        np.nan
    )

    result = 100 - (
        100 / (1 + rs)
    )

    return result.fillna(50)


def add_rsi(df, period=14):
    df = df.copy()

    df["rsi14"] = rsi(
        df["close"],
        period
    )

    return df


# ------------------------------------------------------------
# MACD
# ------------------------------------------------------------

def macd(
    series,
    fast=12,
    slow=26,
    signal=9
):
    fast_ema = ema(
        series,
        fast
    )

    slow_ema = ema(
        series,
        slow
    )

    macd_line = (
        fast_ema -
        slow_ema
    )

    signal_line = ema(
        macd_line,
        signal
    )

    histogram = (
        macd_line -
        signal_line
    )

    return (
        macd_line,
        signal_line,
        histogram
    )


def add_macd(df):
    df = df.copy()

    (
        df["macd"],
        df["macd_signal"],
        df["macd_hist"]
    ) = macd(
        df["close"]
    )

    return df


# ------------------------------------------------------------
# ATR
# ------------------------------------------------------------

def atr(df, period=14):

    high = df["high"]
    low = df["low"]
    close = df["close"]

    previous_close = close.shift(1)

    tr1 = high - low

    tr2 = (
        high -
        previous_close
    ).abs()

    tr3 = (
        low -
        previous_close
    ).abs()

    true_range = pd.concat(
        [
            tr1,
            tr2,
            tr3
        ],
        axis=1
    ).max(axis=1)

    return true_range.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period
    ).mean()


def add_atr(df, period=14):
    df = df.copy()

    df["atr14"] = atr(
        df,
        period
    )

    return df


# ------------------------------------------------------------
# OBV
# ------------------------------------------------------------

def obv(df):

    direction = np.sign(
        df["close"].diff()
    )

    volume = df["volume"]

    values = (
        direction *
        volume
    ).fillna(0)

    return values.cumsum()


def add_obv(df):
    df = df.copy()

    df["obv"] = obv(df)

    return df


# ------------------------------------------------------------
# VOLUME ANALYSIS
# ------------------------------------------------------------

def add_volume_metrics(
    df,
    period=20
):
    df = df.copy()

    df["volume_ma20"] = (
        df["volume"]
        .rolling(period)
        .mean()
    )

    df["volume_ratio"] = (
        df["volume"] /
        df["volume_ma20"]
    )

    return df


# ------------------------------------------------------------
# PRICE POSITION
# ------------------------------------------------------------

def add_price_position(
    df,
    lookback=20
):
    df = df.copy()

    df["rolling_high"] = (
        df["high"]
        .rolling(lookback)
        .max()
    )

    df["rolling_low"] = (
        df["low"]
        .rolling(lookback)
        .min()
    )

    price_range = (
        df["rolling_high"] -
        df["rolling_low"]
    )

    df["range_position"] = (
        (
            df["close"] -
            df["rolling_low"]
        ) /
        price_range.replace(
            0,
            np.nan
        )
    )

    return df


# ------------------------------------------------------------
# MOMENTUM
# ------------------------------------------------------------

def add_momentum(df):
    df = df.copy()

    df["roc"] = (
        df["close"]
        .pct_change(10)
        * 100
    )

    return df


# ------------------------------------------------------------
# ALL INDICATORS
# ------------------------------------------------------------

def calculate_indicators(df):

    if df is None:
        return None

    if df.empty:
        return df

    required = [
        "open",
        "high",
        "low",
        "close",
        "volume"
    ]

    for column in required:
        if column not in df.columns:
            raise ValueError(
                f"Eksik kolon: {column}"
            )

    result = df.copy()

    result = add_ema(
        result
    )

    result = add_rsi(
        result
    )

    result = add_macd(
        result
    )

    result = add_atr(
        result
    )

    result = add_obv(
        result
    )

    result = add_volume_metrics(
        result
    )

    result = add_price_position(
        result
    )

    result = add_momentum(
        result
    )

    return result


# ------------------------------------------------------------
# LATEST INDICATOR SNAPSHOT
# ------------------------------------------------------------

def latest_indicators(df):

    if df is None or df.empty:
        return {}

    df = calculate_indicators(
        df
    )

    row = df.iloc[-1]

    return {
        "price": float(
            row["close"]
        ),

        "ema20": float(
            row["ema20"]
        ),

        "ema50": float(
            row["ema50"]
        ),

        "rsi": float(
            row["rsi14"]
        ),

        "macd": float(
            row["macd"]
        ),

        "macd_signal": float(
            row["macd_signal"]
        ),

        "macd_hist": float(
            row["macd_hist"]
        ),

        "atr": float(
            row["atr14"]
        ),

        "obv": float(
            row["obv"]
        ),

        "volume_ratio": float(
            row["volume_ratio"]
        ),

        "roc": float(
            row["roc"]
        ),

        "range_position": float(
            row["range_position"]
        )
    }


# ------------------------------------------------------------
# TREND CLASSIFICATION
# ------------------------------------------------------------

def classify_trend(snapshot):

    if not snapshot:
        return "UNKNOWN"

    price = snapshot["price"]
    ema20 = snapshot["ema20"]
    ema50 = snapshot["ema50"]

    if (
        price > ema20 >
        ema50
    ):
        return "UP"

    if (
        price < ema20 <
        ema50
    ):
        return "DOWN"

    return "SIDEWAYS"


# ------------------------------------------------------------
# MOMENTUM CLASSIFICATION
# ------------------------------------------------------------

def classify_momentum(snapshot):

    if not snapshot:
        return "UNKNOWN"

    macd_hist = snapshot[
        "macd_hist"
    ]

    rsi_value = snapshot[
        "rsi"
    ]

    if (
        macd_hist > 0 and
        rsi_value >= 50
    ):
        return "STRONG"

    if (
        macd_hist > 0 or
        rsi_value >= 50
    ):
        return "POSITIVE"

    if (
        macd_hist < 0 and
        rsi_value < 50
    ):
        return "WEAK"

    return "NEGATIVE"
