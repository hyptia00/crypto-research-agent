# ============================================================
# CRYPTO RESEARCH AGENT
# TECHNICAL INDICATORS ENGINE
# ============================================================

from config import (
    EMA_FAST,
    EMA_SLOW,
    EMA_TREND,
    RSI_PERIOD,
    MACD_FAST,
    MACD_SLOW,
    MACD_SIGNAL,
    ATR_PERIOD,
    VOLUME_LOOKBACK,
    STRONG_VOLUME_MULTIPLIER,
    NORMAL_VOLUME_MULTIPLIER,
    WEAK_VOLUME_MULTIPLIER,
)


# ------------------------------------------------------------
# BASIC HELPERS
# ------------------------------------------------------------

def _closes(candles):
    return [float(x["close"]) for x in candles]


def _highs(candles):
    return [float(x["high"]) for x in candles]


def _lows(candles):
    return [float(x["low"]) for x in candles]


def _volumes(candles):
    return [float(x["volume"]) for x in candles]


# ------------------------------------------------------------
# EMA
# ------------------------------------------------------------

def ema(values, period):
    """
    Exponential Moving Average.

    Son EMA değerini döndürür.
    """

    values = [float(x) for x in values]

    if not values:
        return None

    if len(values) < period:
        return sum(values) / len(values)

    multiplier = 2 / (period + 1)

    current = sum(values[:period]) / period

    for price in values[period:]:
        current = (
            (price - current) * multiplier
            + current
        )

    return current


def ema_series(values, period):
    """
    Bütün EMA serisini döndürür.
    """

    values = [float(x) for x in values]

    if not values:
        return []

    if len(values) < period:
        return [sum(values) / len(values)] * len(values)

    multiplier = 2 / (period + 1)

    result = [None] * (period - 1)

    current = sum(values[:period]) / period

    result.append(current)

    for price in values[period:]:
        current = (
            (price - current) * multiplier
            + current
        )

        result.append(current)

    return result


# ------------------------------------------------------------
# RSI
# ------------------------------------------------------------

def rsi(values, period=14):
    """
    Wilder RSI.

    Son RSI değerini döndürür.
    """

    values = [float(x) for x in values]

    if len(values) <= period:
        return 50.0

    gains = []
    losses = []

    for i in range(1, len(values)):

        change = values[i] - values[i - 1]

        if change > 0:
            gains.append(change)
            losses.append(0.0)

        else:
            gains.append(0.0)
            losses.append(abs(change))

    avg_gain = sum(
        gains[:period]
    ) / period

    avg_loss = sum(
        losses[:period]
    ) / period

    for i in range(period, len(gains)):

        avg_gain = (
            (avg_gain * (period - 1))
            + gains[i]
        ) / period

        avg_loss = (
            (avg_loss * (period - 1))
            + losses[i]
        ) / period

    if avg_loss == 0:

        if avg_gain == 0:
            return 50.0

        return 100.0

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))


# ------------------------------------------------------------
# MACD
# ------------------------------------------------------------

def macd(
    values,
    fast=12,
    slow=26,
    signal=9
):
    """
    MACD hesaplar.

    Dönen:

    {
        "macd": ...,
        "signal": ...,
        "histogram": ...
    }
    """

    values = [float(x) for x in values]

    if len(values) < slow:

        return {
            "macd": 0.0,
            "signal": 0.0,
            "histogram": 0.0,
        }

    fast_series = ema_series(
        values,
        fast
    )

    slow_series = ema_series(
        values,
        slow
    )

    macd_series = []

    for i in range(len(values)):

        if (
            fast_series[i] is None
            or slow_series[i] is None
        ):
            macd_series.append(None)

        else:
            macd_series.append(
                fast_series[i]
                - slow_series[i]
            )

    valid = [
        x for x in macd_series
        if x is not None
    ]

    if not valid:

        return {
            "macd": 0.0,
            "signal": 0.0,
            "histogram": 0.0,
        }

    signal_value = ema(
        valid,
        signal
    )

    macd_value = valid[-1]

    histogram = (
        macd_value
        - signal_value
    )

    return {
        "macd": macd_value,
        "signal": signal_value,
        "histogram": histogram,
    }


# ------------------------------------------------------------
# TRUE RANGE
# ------------------------------------------------------------

def true_ranges(candles):

    if not candles:
        return []

    result = []

    for i, candle in enumerate(candles):

        high = float(candle["high"])
        low = float(candle["low"])

        if i == 0:

            tr = high - low

        else:

            previous_close = float(
                candles[i - 1]["close"]
            )

            tr = max(
                high - low,
                abs(high - previous_close),
                abs(low - previous_close),
            )

        result.append(tr)

    return result


# ------------------------------------------------------------
# ATR
# ------------------------------------------------------------

def atr(candles, period=14):
    """
    Average True Range.
    """

    trs = true_ranges(candles)

    if not trs:
        return 0.0

    if len(trs) < period:
        return sum(trs) / len(trs)

    value = sum(
        trs[:period]
    ) / period

    for tr in trs[period:]:

        value = (
            (value * (period - 1))
            + tr
        ) / period

    return value


# ------------------------------------------------------------
# ATR PERCENT
# ------------------------------------------------------------

def atr_percent(candles, period=14):

    if not candles:
        return 0.0

    price = float(
        candles[-1]["close"]
    )

    if price <= 0:
        return 0.0

    value = atr(
        candles,
        period
    )

    return (
        value / price
    ) * 100


# ------------------------------------------------------------
# VOLUME ANALYSIS
# ------------------------------------------------------------

def volume_analysis(
    candles,
    lookback=20
):
    """
    Güncel hacmi ortalama hacimle karşılaştırır.
    """

    if not candles:

        return {
            "current": 0.0,
            "average": 0.0,
            "ratio": 0.0,
            "state": "UNKNOWN",
        }

    volumes = _volumes(candles)

    current = volumes[-1]

    previous = volumes[
        -lookback - 1:-1
    ]

    if not previous:

        previous = volumes[:-1]

    if not previous:

        average = current

    else:

        average = (
            sum(previous)
            / len(previous)
        )

    if average <= 0:

        ratio = 0.0

    else:

        ratio = current / average

    if ratio >= STRONG_VOLUME_MULTIPLIER:

        state = "STRONG"

    elif ratio >= NORMAL_VOLUME_MULTIPLIER:

        state = "NORMAL"

    elif ratio >= WEAK_VOLUME_MULTIPLIER:

        state = "WEAK"

    else:

        state = "VERY_WEAK"

    return {
        "current": current,
        "average": average,
        "ratio": ratio,
        "state": state,
    }


# ------------------------------------------------------------
# OBV
# ------------------------------------------------------------

def obv(candles):

    if not candles:
        return 0.0

    value = 0.0

    for i in range(1, len(candles)):

        current_close = float(
            candles[i]["close"]
        )

        previous_close = float(
            candles[i - 1]["close"]
        )

        volume = float(
            candles[i]["volume"]
        )

        if current_close > previous_close:

            value += volume

        elif current_close < previous_close:

            value -= volume

    return value


# ------------------------------------------------------------
# MOMENTUM
# ------------------------------------------------------------

def momentum(
    values,
    period=10
):

    values = [float(x) for x in values]

    if len(values) <= period:
        return 0.0

    previous = values[-period - 1]

    if previous == 0:
        return 0.0

    return (
        (values[-1] - previous)
        / previous
    ) * 100


# ------------------------------------------------------------
# PRICE POSITION
# ------------------------------------------------------------

def price_vs_ema(
    price,
    ema20_value,
    ema50_value
):
    """
    Fiyatın EMA'lara göre konumunu belirler.
    """

    if price > ema20_value:

        above_ema20 = True

    else:

        above_ema20 = False

    if price > ema50_value:

        above_ema50 = True

    else:

        above_ema50 = False

    if (
        above_ema20
        and above_ema50
    ):

        state = "ABOVE_BOTH"

    elif (
        not above_ema20
        and not above_ema50
    ):

        state = "BELOW_BOTH"

    else:

        state = "BETWEEN"

    return {
        "above_ema20": above_ema20,
        "above_ema50": above_ema50,
        "state": state,
    }


# ------------------------------------------------------------
# TREND
# ------------------------------------------------------------

def trend_from_emas(
    price,
    ema20_value,
    ema50_value,
    ema200_value=None
):
    """
    EMA yapısından basit trend sınıflandırması.
    """

    if ema200_value is not None:

        if (
            price > ema20_value
            and ema20_value > ema50_value
            and ema50_value > ema200_value
        ):

            return "STRONG_UP"

        if (
            price < ema20_value
            and ema20_value < ema50_value
            and ema50_value < ema200_value
        ):

            return "STRONG_DOWN"

    if (
        price > ema20_value
        and ema20_value > ema50_value
    ):

        return "UP"

    if (
        price < ema20_value
        and ema20_value < ema50_value
    ):

        return "DOWN"

    return "SIDEWAYS"


# ------------------------------------------------------------
# CANDLE INFORMATION
# ------------------------------------------------------------

def candle_analysis(candle):

    open_price = float(
        candle["open"]
    )

    high = float(
        candle["high"]
    )

    low = float(
        candle["low"]
    )

    close = float(
        candle["close"]
    )

    body = abs(
        close - open_price
    )

    candle_range = high - low

    if candle_range <= 0:

        body_percent = 0.0

    else:

        body_percent = (
            body / candle_range
        ) * 100

    if close > open_price:

        direction = "BULLISH"

    elif close < open_price:

        direction = "BEARISH"

    else:

        direction = "DOJI"

    upper_wick = (
        high - max(
            open_price,
            close
        )
    )

    lower_wick = (
        min(
            open_price,
            close
        ) - low
    )

    return {
        "direction": direction,
        "body": body,
        "range": candle_range,
        "body_percent": body_percent,
        "upper_wick": upper_wick,
        "lower_wick": lower_wick,
    }


# ------------------------------------------------------------
# COMPLETE INDICATOR SNAPSHOT
# ------------------------------------------------------------

def calculate_indicators(candles):

    if not candles:

        raise ValueError(
            "Indicator hesaplamak için candle verisi gerekli."
        )

    closes = _closes(candles)

    price = closes[-1]

    ema20_value = ema(
        closes,
        EMA_FAST
    )

    ema50_value = ema(
        closes,
        EMA_SLOW
    )

    ema200_value = ema(
        closes,
        EMA_TREND
    )

    rsi_value = rsi(
        closes,
        RSI_PERIOD
    )

    macd_data = macd(
        closes,
        MACD_FAST,
        MACD_SLOW,
        MACD_SIGNAL
    )

    atr_value = atr(
        candles,
        ATR_PERIOD
    )

    atr_percent_value = atr_percent(
        candles,
        ATR_PERIOD
    )

    volume_data = volume_analysis(
        candles,
        VOLUME_LOOKBACK
    )

    obv_value = obv(candles)

    momentum_value = momentum(
        closes
    )

    price_position = price_vs_ema(
        price,
        ema20_value,
        ema50_value
    )

    trend = trend_from_emas(
        price,
        ema20_value,
        ema50_value,
        ema200_value
    )

    last_candle = candle_analysis(
        candles[-1]
    )

    return {
        "price": price,

        "ema20": ema20_value,

        "ema50": ema50_value,

        "ema200": ema200_value,

        "rsi": rsi_value,

        "macd": macd_data["macd"],

        "macd_signal": macd_data["signal"],

        "macd_histogram": macd_data["histogram"],

        "atr": atr_value,

        "atr_percent": atr_percent_value,

        "volume": volume_data,

        "obv": obv_value,

        "momentum_percent": momentum_value,

        "price_position": price_position,

        "trend": trend,

        "candle": last_candle,
    }


# ------------------------------------------------------------
# SIGNAL COMPONENTS
# ------------------------------------------------------------

def indicator_bias(indicators):

    """
    İndikatörlerden LONG / SHORT / NEUTRAL bias üretir.

    Bu henüz nihai trade sinyali değildir.
    """

    long_points = 0
    short_points = 0

    price = indicators["price"]

    ema20_value = indicators["ema20"]
    ema50_value = indicators["ema50"]

    rsi_value = indicators["rsi"]

    macd_hist = indicators[
        "macd_histogram"
    ]

    # EMA
    if price > ema20_value:
        long_points += 1
    else:
        short_points += 1

    if ema20_value > ema50_value:
        long_points += 1
    else:
        short_points += 1

    # RSI
    if rsi_value >= 50:
        long_points += 1
    else:
        short_points += 1

    # MACD
    if macd_hist > 0:
        long_points += 1
    elif macd_hist < 0:
        short_points += 1

    # Karar
    if long_points > short_points:

        bias = "LONG"

    elif short_points > long_points:

        bias = "SHORT"

    else:

        bias = "NEUTRAL"

    return {
        "bias": bias,
        "long_points": long_points,
        "short_points": short_points,
        "total_points": 4,
    }


# ------------------------------------------------------------
# MULTI-TIMEFRAME INDICATORS
# ------------------------------------------------------------

def calculate_multi_timeframe_indicators(
    multi_data
):
    """
    Örnek:

    {
        "4h": candles,
        "1h": candles,
        "15m": candles,
        "5m": candles,
        "1m": candles
    }
    """

    result = {}

    for timeframe, candles in multi_data.items():

        if not candles:
            continue

        indicators = calculate_indicators(
            candles
        )

        bias = indicator_bias(
            indicators
        )

        result[timeframe] = {
            "indicators": indicators,
            "bias": bias,
        }

    return result


# ------------------------------------------------------------
# TREND ALIGNMENT
# ------------------------------------------------------------

def timeframe_alignment(
    mtf_data
):
    """
    Timeframe yönlerinin birbirleriyle
    uyumunu kontrol eder.
    """

    bullish = 0
    bearish = 0
    neutral = 0

    for data in mtf_data.values():

        bias = data["bias"]["bias"]

        if bias == "LONG":

            bullish += 1

        elif bias == "SHORT":

            bearish += 1

        else:

            neutral += 1

    if bullish > bearish:

        direction = "LONG"

    elif bearish > bullish:

        direction = "SHORT"

    else:

        direction = "NEUTRAL"

    return {
        "direction": direction,
        "bullish": bullish,
        "bearish": bearish,
        "neutral": neutral,
        "timeframes": len(mtf_data),
    }


# ------------------------------------------------------------
# TEST
# ------------------------------------------------------------

if __name__ == "__main__":

    print("=" * 60)
    print("TECHNICAL INDICATORS ENGINE TEST")
    print("=" * 60)

    print()
    print("Modül başarıyla yüklendi.")

    print()
    print("Desteklenen göstergeler:")

    print("- EMA 20")
    print("- EMA 50")
    print("- EMA 200")
    print("- RSI 14")
    print("- MACD")
    print("- ATR")
    print("- ATR %")
    print("- Volume")
    print("- OBV")
    print("- Momentum")
    print("- Candle Analysis")
    print("- Trend")
    print("- Indicator Bias")
    print("- Multi-Timeframe Alignment")

    print()
    print("TEST TAMAMLANDI")
    print("=" * 60)
