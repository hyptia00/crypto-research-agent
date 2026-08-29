# ============================================================
# MARKET INDICATORS
# ============================================================

import numpy as np
import pandas as pd


# ============================================================
# HELPERS
# ============================================================

def _ensure_ohlcv(df):

    if df is None:
        return pd.DataFrame()

    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)

    required = [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    for column in required:

        if column not in df.columns:
            raise ValueError(
                f"Missing OHLCV column: {column}"
            )

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df = df.copy()

    df = df.dropna(
        subset=required
    )

    return df


# ============================================================
# EMA
# ============================================================

def ema(
    series,
    period,
):

    return series.ewm(
        span=period,
        adjust=False,
        min_periods=period,
    ).mean()


# ============================================================
# SMA
# ============================================================

def sma(
    series,
    period,
):

    return series.rolling(
        period
    ).mean()


# ============================================================
# RSI
# ============================================================

def rsi(
    series,
    period=14,
):

    delta = series.diff()

    gain = delta.clip(
        lower=0
    )

    loss = -delta.clip(
        upper=0
    )

    avg_gain = gain.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()

    rs = (
        avg_gain
        /
        avg_loss.replace(
            0,
            np.nan
        )
    )

    result = 100 - (
        100 / (1 + rs)
    )

    # Sürekli yükselen piyasada RSI = 100
    result = result.fillna(
        np.where(
            avg_gain > 0,
            100,
            0
        )
    )

    return result


# ============================================================
# MACD
# ============================================================

def macd(
    series,
    fast=12,
    slow=26,
    signal=9,
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
        fast_ema
        -
        slow_ema
    )

    signal_line = ema(
        macd_line,
        signal
    )

    histogram = (
        macd_line
        -
        signal_line
    )

    return (
        macd_line,
        signal_line,
        histogram,
    )


# ============================================================
# ATR
# ============================================================

def atr(
    df,
    period=14,
):

    previous_close = (
        df["close"].shift(1)
    )

    tr1 = (
        df["high"]
        -
        df["low"]
    )

    tr2 = (
        df["high"]
        -
        previous_close
    ).abs()

    tr3 = (
        df["low"]
        -
        previous_close
    ).abs()

    true_range = pd.concat(
        [
            tr1,
            tr2,
            tr3,
        ],
        axis=1,
    ).max(
        axis=1
    )

    return true_range.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()


# ============================================================
# VOLUME RATIO
# ============================================================

def volume_ratio(
    volume,
    period=20,
):

    average = volume.rolling(
        period
    ).mean()

    return (
        volume
        /
        average.replace(
            0,
            np.nan
        )
    )


# ============================================================
# VWAP
# ============================================================

def vwap(
    df,
):

    typical_price = (
        df["high"]
        +
        df["low"]
        +
        df["close"]
    ) / 3

    cumulative_volume = (
        df["volume"]
        .cumsum()
    )

    cumulative_pv = (
        typical_price
        *
        df["volume"]
    ).cumsum()

    return (
        cumulative_pv
        /
        cumulative_volume.replace(
            0,
            np.nan
        )
    )


# ============================================================
# COMPLETE INDICATORS
# ============================================================

def calculate_indicators(
    df,
):

    df = _ensure_ohlcv(
        df
    )

    if df.empty:
        return df

    # --------------------------------------------------------
    # EMA
    # --------------------------------------------------------

    df["ema20"] = ema(
        df["close"],
        20
    )

    df["ema50"] = ema(
        df["close"],
        50
    )

    df["ema100"] = ema(
        df["close"],
        100
    )

    df["ema200"] = ema(
        df["close"],
        200
    )

    # --------------------------------------------------------
    # SMA
    # --------------------------------------------------------

    df["sma20"] = sma(
        df["close"],
        20
    )

    df["sma50"] = sma(
        df["close"],
        50
    )

    # --------------------------------------------------------
    # RSI
    # --------------------------------------------------------

    df["rsi"] = rsi(
        df["close"],
        14
    )

    # --------------------------------------------------------
    # MACD
    # --------------------------------------------------------

    (
        df["macd"],
        df["macd_signal"],
        df["macd_hist"],
    ) = macd(
        df["close"]
    )

    # --------------------------------------------------------
    # ATR
    # --------------------------------------------------------

    df["atr"] = atr(
        df,
        14
    )

    # --------------------------------------------------------
    # ATR %
    # --------------------------------------------------------

    df["atr_percent"] = (
        df["atr"]
        /
        df["close"]
    ) * 100

    # --------------------------------------------------------
    # VOLUME
    # --------------------------------------------------------

    df["volume_ma20"] = (
        df["volume"]
        .rolling(20)
        .mean()
    )

    df["volume_ratio"] = (
        volume_ratio(
            df["volume"],
            20
        )
    )

    # --------------------------------------------------------
    # VWAP
    # --------------------------------------------------------

    df["vwap"] = vwap(
        df
    )

    # --------------------------------------------------------
    # MOMENTUM
    # --------------------------------------------------------

    df["roc"] = (
        df["close"]
        .pct_change(10)
        * 100
    )

    # --------------------------------------------------------
    # CANDLE RANGE
    # --------------------------------------------------------

    df["candle_range"] = (
        df["high"]
        -
        df["low"]
    )

    df["body"] = (
        df["close"]
        -
        df["open"]
    ).abs()

    df["body_ratio"] = (
        df["body"]
        /
        df["candle_range"].replace(
            0,
            np.nan
        )
    )

    # --------------------------------------------------------
    # TREND FLAGS
    # --------------------------------------------------------

    df["bullish_trend"] = (
        (df["close"] > df["ema20"])
        &
        (df["ema20"] > df["ema50"])
    )

    df["bearish_trend"] = (
        (df["close"] < df["ema20"])
        &
        (df["ema20"] < df["ema50"])
    )

    # --------------------------------------------------------
    # MACD FLAGS
    # --------------------------------------------------------

    df["macd_bullish"] = (
        df["macd_hist"] > 0
    )

    df["macd_bearish"] = (
        df["macd_hist"] < 0
    )

    return df


# ============================================================
# LATEST VALUES
# ============================================================

def latest_indicators(
    df,
):

    data = calculate_indicators(
        df
    )

    if data.empty:
        return {}

    row = data.iloc[-1]

    return {

        "price":
            float(row["close"]),

        "open":
            float(row["open"]),

        "high":
            float(row["high"]),

        "low":
            float(row["low"]),

        "volume":
            float(row["volume"]),

        "ema20":
            _safe_value(
                row["ema20"]
            ),

        "ema50":
            _safe_value(
                row["ema50"]
            ),

        "ema100":
            _safe_value(
                row["ema100"]
            ),

        "ema200":
            _safe_value(
                row["ema200"]
            ),

        "sma20":
            _safe_value(
                row["sma20"]
            ),

        "sma50":
            _safe_value(
                row["sma50"]
            ),

        "rsi":
            _safe_value(
                row["rsi"]
            ),

        "macd":
            _safe_value(
                row["macd"]
            ),

        "macd_signal":
            _safe_value(
                row["macd_signal"]
            ),

        "macd_hist":
            _safe_value(
                row["macd_hist"]
            ),

        "atr":
            _safe_value(
                row["atr"]
            ),

        "atr_percent":
            _safe_value(
                row["atr_percent"]
            ),

        "volume_ma20":
            _safe_value(
                row["volume_ma20"]
            ),

        "volume_ratio":
            _safe_value(
                row["volume_ratio"]
            ),

        "vwap":
            _safe_value(
                row["vwap"]
            ),

        "roc":
            _safe_value(
                row["roc"]
            ),

        "body_ratio":
            _safe_value(
                row["body_ratio"]
            ),

        "bullish_trend":
            bool(
                row["bullish_trend"]
            ),

        "bearish_trend":
            bool(
                row["bearish_trend"]
            ),

        "macd_bullish":
            bool(
                row["macd_bullish"]
            ),

        "macd_bearish":
            bool(
                row["macd_bearish"]
            ),
    }


def _safe_value(
    value
):

    try:

        value = float(value)

        if np.isnan(value):
            return None

        if np.isinf(value):
            return None

        return value

    except (
        TypeError,
        ValueError,
    ):

        return None
