import json
import urllib.request
import urllib.parse
import time
import math

BASE_URL = "https://data-api.binance.vision"

WATCHLIST = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "DOTUSDT",
    "NEARUSDT",
    "JUPUSDT",
    "MOVRUSDT",
    "TNSRUSDT",
]

KLINE_LIMIT = 200
SCAN_LIMIT = 30
MIN_QUOTE_VOLUME = 5_000_000

# =========================================================
# API
# =========================================================

def get_json(path, params=None, retries=5):

    if params:
        path += "?" + urllib.parse.urlencode(params)

    url = BASE_URL + path

    for attempt in range(retries):

        try:

            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "CryptoResearchAgent/3.0"
                }
            )

            with urllib.request.urlopen(
                request,
                timeout=20
            ) as response:

                return json.loads(
                    response.read().decode()
                )

        except Exception as e:

            message = str(e)

            # Binance rate limit
            if "429" in message:

                wait_time = min(
                    10 * (attempt + 1),
                    60
                )

                print(
                    f"   API limit. "
                    f"{wait_time}s bekleniyor..."
                )

                time.sleep(wait_time)

            else:

                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise e


def get_klines(symbol, interval, limit=KLINE_LIMIT):

    return get_json(
        "/api/v3/klines",
        {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
    )


# =========================================================
# INDICATORS
# =========================================================

def ema(values, period):

    if len(values) < period:
        return None

    multiplier = 2 / (period + 1)

    result = sum(
        values[:period]
    ) / period

    for price in values[period:]:

        result = (
            (price - result)
            * multiplier
            + result
        )

    return result


def sma(values, period):

    if len(values) < period:
        return None

    return sum(
        values[-period:]
    ) / period


def rsi(values, period=14):

    if len(values) < period + 1:
        return None

    gains = []
    losses = []

    for i in range(1, len(values)):

        change = (
            values[i]
            - values[i - 1]
        )

        gains.append(
            max(change, 0)
        )

        losses.append(
            max(-change, 0)
        )

    avg_gain = (
        sum(gains[:period])
        / period
    )

    avg_loss = (
        sum(losses[:period])
        / period
    )

    for i in range(
        period,
        len(gains)
    ):

        avg_gain = (
            avg_gain * (period - 1)
            + gains[i]
        ) / period

        avg_loss = (
            avg_loss * (period - 1)
            + losses[i]
        ) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss

    return 100 - (
        100 / (1 + rs)
    )


def macd(values):

    if len(values) < 50:
        return None, None, None

    ema12_values = []
    ema26_values = []

    multiplier12 = 2 / 13
    multiplier26 = 2 / 27

    e12 = sum(
        values[:12]
    ) / 12

    e26 = sum(
        values[:26]
    ) / 26

    for price in values[12:]:

        e12 = (
            (price - e12)
            * multiplier12
            + e12
        )

        ema12_values.append(e12)

    for price in values[26:]:

        e26 = (
            (price - e26)
            * multiplier26
            + e26
        )

    length = min(
        len(ema12_values),
        len(values) - 26
    )

    macd_values = []

    for i in range(length):

        macd_values.append(
            ema12_values[-length + i]
            - e26
        )

    if len(macd_values) < 9:
        return None, None, None

    signal = ema(
        macd_values,
        9
    )

    if signal is None:
        return None, None, None

    histogram = (
        macd_values[-1]
        - signal
    )

    return (
        macd_values[-1],
        signal,
        histogram
    )


def atr(
    highs,
    lows,
    closes,
    period=14
):

    if len(closes) < period + 1:
        return None

    ranges = []

    for i in range(
        1,
        len(closes)
    ):

        value = max(
            highs[i] - lows[i],
            abs(
                highs[i]
                - closes[i - 1]
            ),
            abs(
                lows[i]
                - closes[i - 1]
            )
        )

        ranges.append(value)

    return (
        sum(ranges[-period:])
        / period
    )


# =========================================================
# DATA
# =========================================================

def parse_klines(data):

    opens = [
        float(x[1])
        for x in data
    ]

    highs = [
        float(x[2])
        for x in data
    ]

    lows = [
        float(x[3])
        for x in data
    ]

    closes = [
        float(x[4])
        for x in data
    ]

    volumes = [
        float(x[5])
        for x in data
    ]

    return (
        opens,
        highs,
        lows,
        closes,
        volumes
    )


# =========================================================
# TIMEFRAME ANALYSIS
# =========================================================

def timeframe_analysis(data):

    (
        opens,
        highs,
        lows,
        closes,
        volumes
    ) = parse_klines(data)

    price = closes[-1]

    ema20 = ema(
        closes,
        20
    )

    ema50 = ema(
        closes,
        50
    )

    rsi14 = rsi(
        closes,
        14
    )

    (
        macd_value,
        macd_signal,
        macd_hist
    ) = macd(closes)

    atr14 = atr(
        highs,
        lows,
        closes
    )

    if (
        ema20
        and ema50
        and price > ema20
        and ema20 > ema50
    ):

        trend = "YUKSELIS"

    elif (
        ema20
        and ema50
        and price < ema20
        and ema20 < ema50
    ):

        trend = "DUSUS"

    else:

        trend = "YATAY"

    return {
        "price": price,
        "ema20": ema20,
        "ema50": ema50,
        "rsi": rsi14,
        "macd": macd_value,
        "macd_signal": macd_signal,
        "macd_hist": macd_hist,
        "atr": atr14,
        "trend": trend,
        "opens": opens,
        "highs": highs,
        "lows": lows,
        "closes": closes,
        "volumes": volumes
    }


# =========================================================
# SUPPORT / RESISTANCE
# =========================================================

def levels(info):

    price = info["price"]
    atr_value = info["atr"]

    lows = info["lows"][-60:]
    highs = info["highs"][-60:]

    supports = [
        x for x in lows
        if x < price
    ]

    resistances = [
        x for x in highs
        if x > price
    ]

    if supports:

        support = max(
            supports
        )

    else:

        support = (
            price
            - atr_value * 2
        )

    if resistances:

        resistance = min(
            resistances
        )

    else:

        resistance = (
            price
            + atr_value * 2
        )

    return (
        support,
        resistance
    )


# =========================================================
# SWING STRUCTURE
# =========================================================

def swing_levels(info):

    highs = info["highs"]
    lows = info["lows"]

    swing_highs = []
    swing_lows = []

    start = max(
        2,
        len(highs) - 60
    )

    end = len(highs) - 2

    for i in range(
        start,
        end
    ):

        if (
            highs[i] > highs[i - 1]
            and highs[i] > highs[i + 1]
        ):

            swing_highs.append(
                highs[i]
            )

        if (
            lows[i] < lows[i - 1]
            and lows[i] < lows[i + 1]
        ):

            swing_lows.append(
                lows[i]
            )

    last_swing_high = (
        swing_highs[-1]
        if swing_highs
        else max(highs[-20:])
    )

    last_swing_low = (
        swing_lows[-1]
        if swing_lows
        else min(lows[-20:])
    )

    return (
        last_swing_high,
        last_swing_low
    )


# =========================================================
# VOLUME
# =========================================================

def volume_ratio(info):

    volumes = info["volumes"]

    average = sma(
        volumes[:-1],
        20
    )

    if not average:
        return 0

    return (
        volumes[-1]
        / average
    )


# =========================================================
# PRICE ACTION
# =========================================================

def price_action(info):

    highs = info["highs"]
    lows = info["lows"]
    closes = info["closes"]
    volumes = info["volumes"]

    price = closes[-1]

    atr_value = info["atr"]

    if not atr_value:
        atr_value = price * 0.01

    recent_high = max(
        highs[-20:-1]
    )

    recent_low = min(
        lows[-20:-1]
    )

    previous_high = max(
        highs[-10:-2]
    )

    previous_low = min(
        lows[-10:-2]
    )

    avg_volume = sma(
        volumes[:-1],
        20
    )

    current_volume = volumes[-1]

    if avg_volume:
        vol_ratio = (
            current_volume
            / avg_volume
        )
    else:
        vol_ratio = 0

    # -----------------------------------------------------
    # LIQUIDITY SWEEP
    # -----------------------------------------------------

    bullish_sweep = (
        lows[-1] < previous_low
        and closes[-1] > previous_low
    )

    bearish_sweep = (
        highs[-1] > previous_high
        and closes[-1] < previous_high
    )

    # -----------------------------------------------------
    # BREAKOUT
    # -----------------------------------------------------

    bullish_breakout = (
        closes[-1] > recent_high
    )

    bearish_breakdown = (
        closes[-1] < recent_low
    )

    # -----------------------------------------------------
    # RETEST
    # -----------------------------------------------------

    bullish_retest = (
        lows[-1] <= recent_high * 1.003
        and closes[-1] > recent_high
    )

    bearish_retest = (
        highs[-1] >= recent_low * 0.997
        and closes[-1] < recent_low
    )

    # -----------------------------------------------------
    # CANDLE STRENGTH
    # -----------------------------------------------------

    candle_range = (
        highs[-1]
        - lows[-1]
    )

    if candle_range > 0:

        body = abs(
            closes[-1]
            - info["opens"][-1]
        )

        body_ratio = (
            body
            / candle_range
        )

    else:

        body_ratio = 0

    bullish_candle = (
        closes[-1]
        > info["opens"][-1]
        and body_ratio >= 0.55
    )

    bearish_candle = (
        closes[-1]
        < info["opens"][-1]
        and body_ratio >= 0.55
    )

    # -----------------------------------------------------
    # SCORES
    # -----------------------------------------------------

    long_score = 0
    short_score = 0

    long_reasons = []
    short_reasons = []

    if bullish_sweep:

        long_score += 2

        long_reasons.append(
            "Likidite sweep yukari"
        )

    if bearish_sweep:

        short_score += 2

        short_reasons.append(
            "Likidite sweep asagi"
        )

    if bullish_breakout:

        long_score += 2

        long_reasons.append(
            "Bullish breakout"
        )

    if bearish_breakdown:

        short_score += 2

        short_reasons.append(
            "Bearish breakdown"
        )

    if bullish_retest:

        long_score += 1

        long_reasons.append(
            "Breakout retest"
        )

    if bearish_retest:

        short_score += 1

        short_reasons.append(
            "Breakdown retest"
        )

    if bullish_candle:

        long_score += 1

        long_reasons.append(
            "Guclu bullish candle"
        )

    if bearish_candle:

        short_score += 1

        short_reasons.append(
            "Guclu bearish candle"
        )

    if vol_ratio >= 1.5:

        if bullish_breakout:

            long_score += 1

            long_reasons.append(
                f"Hacim breakout ({vol_ratio:.2f}x)"
            )

        if bearish_breakdown:

            short_score += 1

            short_reasons.append(
                f"Hacim breakdown ({vol_ratio:.2f}x)"
            )

    return {
        "long_score": long_score,
        "short_score": short_score,
        "long_reasons": long_reasons,
        "short_reasons": short_reasons,
        "bullish_sweep": bullish_sweep,
        "bearish_sweep": bearish_sweep,
        "bullish_breakout": bullish_breakout,
        "bearish_breakdown": bearish_breakdown,
        "bullish_retest": bullish_retest,
        "bearish_retest": bearish_retest,
        "recent_high": recent_high,
        "recent_low": recent_low,
        "vol_ratio": vol_ratio
    }


# =========================================================
# MARKET REGIME
# =========================================================

def market_regime(btc_4h):

    if not btc_4h:
        return "UNKNOWN"

    trend = btc_4h["trend"]
    rsi_value = btc_4h["rsi"]

    if (
        trend == "YUKSELIS"
        and rsi_value is not None
        and rsi_value >= 50
    ):

        return "RISK_ON"

    if (
        trend == "DUSUS"
        and rsi_value is not None
        and rsi_value <= 50
    ):

        return "RISK_OFF"

    return "NEUTRAL"


# =========================================================
# TRADE SETUP
# =========================================================

def trade_levels(
    signal,
    price,
    support,
    resistance,
    atr_value
):

    if not atr_value:
        atr_value = price * 0.01

    if signal == "LONG":

        stop = min(
            support - atr_value * 0.20,
            price - atr_value * 1.20
        )

        risk = price - stop

        tp1 = (
            price
            + risk * 1.5
        )

        tp2 = (
            price
            + risk * 2.5
        )

    else:

        stop = max(
            resistance + atr_value * 0.20,
            price + atr_value * 1.20
        )

        risk = stop - price

        tp1 = (
            price
            - risk * 1.5
        )

        tp2 = (
            price
            - risk * 2.5
        )

    rr = (
        2.5
        if risk > 0
        else 0
    )

    return (
        price,
        stop,
        tp1,
        tp2,
        rr
    )


# =========================================================
# SYMBOL ANALYSIS
# =========================================================

def analyze_symbol(
    symbol,
    data_1h,
    data_4h,
    btc_regime="NEUTRAL"
):

    one_h = timeframe_analysis(
        data_1h
    )

    four_h = timeframe_analysis(
        data_4h
    )

    price = one_h["price"]

    support, resistance = levels(
        one_h
    )

    (
        swing_high,
        swing_low
    ) = swing_levels(
        one_h
    )

    vol_ratio = volume_ratio(
        one_h
    )

    pa = price_action(
        one_h
    )

    long_score = 0
    short_score = 0

    long_reasons = []
    short_reasons = []

    # -----------------------------------------------------
    # TREND
    # -----------------------------------------------------

    if four_h["trend"] == "YUKSELIS":

        long_score += 2

        long_reasons.append(
            "4H trend yukselis"
        )

    elif four_h["trend"] == "DUSUS":

        short_score += 2

        short_reasons.append(
            "4H trend dusus"
        )

    if one_h["trend"] == "YUKSELIS":

        long_score += 2

        long_reasons.append(
            "1H trend yukselis"
        )

    elif one_h["trend"] == "DUSUS":

        short_score += 2

        short_reasons.append(
            "1H trend dusus"
        )

    # -----------------------------------------------------
    # RSI
    # -----------------------------------------------------

    rsi_value = one_h["rsi"]

    if rsi_value is not None:

        if 45 <= rsi_value <= 68:

            long_score += 1

            long_reasons.append(
                f"RSI uygun ({rsi_value:.1f})"
            )

        if 32 <= rsi_value <= 55:

            short_score += 1

            short_reasons.append(
                f"RSI uygun ({rsi_value:.1f})"
            )

    # -----------------------------------------------------
    # MACD
    # -----------------------------------------------------

    histogram = one_h["macd_hist"]

    if histogram is not None:

        if histogram > 0:

            long_score += 1

            long_reasons.append(
                "MACD momentum pozitif"
            )

        elif histogram < 0:

            short_score += 1

            short_reasons.append(
                "MACD momentum negatif"
            )

    # -----------------------------------------------------
    # VOLUME
    # -----------------------------------------------------

    if vol_ratio >= 1.2:

        long_score += 1
        short_score += 1

        long_reasons.append(
            f"Hacim guclu ({vol_ratio:.2f}x)"
        )

        short_reasons.append(
            f"Hacim guclu ({vol_ratio:.2f}x)"
        )

    # -----------------------------------------------------
    # PRICE ACTION
    # -----------------------------------------------------

    long_score += pa["long_score"]
    short_score += pa["short_score"]

    long_reasons.extend(
        pa["long_reasons"]
    )

    short_reasons.extend(
        pa["short_reasons"]
    )

    # -----------------------------------------------------
    # BTC REGIME
    # -----------------------------------------------------

    if btc_regime == "RISK_ON":

        long_score += 1

        long_reasons.append(
            "BTC risk-on"
        )

    elif btc_regime == "RISK_OFF":

        short_score += 1

        short_reasons.append(
            "BTC risk-off"
        )

    # -----------------------------------------------------
    # MARKET STRUCTURE
    # -----------------------------------------------------

    if (
        price > swing_high
        and one_h["trend"] == "YUKSELIS"
    ):

        long_score += 1

        long_reasons.append(
            "Swing high kirildi"
        )

    if (
        price < swing_low
        and one_h["trend"] == "DUSUS"
    ):

        short_score += 1

        short_reasons.append(
            "Swing low kirildi"
        )

    # -----------------------------------------------------
    # SIGNAL
    # -----------------------------------------------------

    signal = "BEKLE"

    score = max(
        long_score,
        short_score
    )

    reasons = []

    entry = 0
    stop = 0
    tp1 = 0
    tp2 = 0
    rr = 0

    # Daha kaliteli sinyal için
    # price action veya güçlü trend şartı.

    long_valid = (
        long_score >= 7
        and (
            pa["long_score"] >= 2
            or (
                four_h["trend"]
                == "YUKSELIS"
                and one_h["trend"]
                == "YUKSELIS"
            )
        )
    )

    short_valid = (
        short_score >= 7
        and (
            pa["short_score"] >= 2
            or (
                four_h["trend"]
                == "DUSUS"
                and one_h["trend"]
                == "DUSUS"
            )
        )
    )

    # BTC risk filtresi
    if btc_regime == "RISK_OFF":
        long_valid = False

    if btc_regime == "RISK_ON":
        short_valid = False

    if long_valid and (
        long_score > short_score
    ):

        signal = "LONG"

        score = long_score

        reasons = long_reasons

        (
            entry,
            stop,
            tp1,
            tp2,
            rr
        ) = trade_levels(
            "LONG",
            price,
            support,
            resistance,
            one_h["atr"]
        )

    elif short_valid and (
        short_score > long_score
    ):

        signal = "SHORT"

        score = short_score

        reasons = short_reasons

        (
            entry,
            stop,
            tp1,
            tp2,
            rr
        ) = trade_levels(
            "SHORT",
            price,
            support,
            resistance,
            one_h["atr"]
        )

    # -----------------------------------------------------
    # QUALITY
    # -----------------------------------------------------

    if signal in (
        "LONG",
        "SHORT"
    ):

        if score >= 10:
            quality = "A+"

        elif score >= 8:
            quality = "A"

        elif score >= 7:
            quality = "B"

        else:
            quality = "C"

    else:

        quality = "-"

    # -----------------------------------------------------
    # ENTRY STATUS
    # -----------------------------------------------------

    entry_status = "AKTIF"

    if signal == "LONG":

        if price > entry * 1.015:

            entry_status = "KACTI"

    elif signal == "SHORT":

        if price < entry * 0.985:

            entry_status = "KACTI"

    return {

        "symbol": symbol.replace(
            "USDT",
            ""
        ),

        "signal": signal,

        "score": score,

        "quality": quality,

        "price": price,

        "entry": entry,

        "stop": stop,

        "tp1": tp1,

        "tp2": tp2,

        "rr": rr,

        "rsi": rsi_value,

        "volume_ratio": vol_ratio,

        "trend_1h": one_h["trend"],

        "trend_4h": four_h["trend"],

        "support": support,

        "resistance": resistance,

        "swing_high": swing_high,

        "swing_low": swing_low,

        "pa_long": pa["long_score"],

        "pa_short": pa["short_score"],

        "btc_regime": btc_regime,

        "entry_status": entry_status,

        "reasons": reasons
    }


# =========================================================
# PRICE FORMAT
# =========================================================

def price_format(value):

    if value is None:
        return "-"

    if value >= 100:

        return f"${value:,.2f}"

    if value >= 1:

        return f"${value:.4f}"

    if value >= 0.01:

        return f"${value:.6f}"

    return f"${value:.8f}"


# =========================================================
# MARKET SCANNER
# =========================================================

def get_market_symbols():

    data = get_json(
        "/api/v3/ticker/24hr"
    )

    symbols = []

    for item in data:

        symbol = item.get(
            "symbol",
            ""
        )

        if not symbol.endswith(
            "USDT"
        ):

            continue

        try:

            volume = float(
                item.get(
                    "quoteVolume",
                    0
                )
            )

        except:

            continue

        if volume < MIN_QUOTE_VOLUME:

            continue

        symbols.append(
            (
                symbol,
                volume
            )
        )

    symbols.sort(
        key=lambda x: x[1],
        reverse=True
    )

    return [
        x[0]
        for x in symbols[:SCAN_LIMIT]
    ]


# =========================================================
# BACKTEST
# =========================================================

def aggregate_4h_from_1h(data):

    if len(data) < 4:
        return []

    result = []

    for i in range(
        0,
        len(data) - 3,
        4
    ):

        block = data[
            i:i + 4
        ]

        if len(block) < 4:
            continue

        first = block[0]
        last = block[-1]

        candle = [
            first[0],
            first[1],
            max(
                float(x[2])
                for x in block
            ),
            min(
                float(x[3])
                for x in block
            ),
            last[4],
            sum(
                float(x[5])
                for x in block
            ),
            last[6],
            last[7],
            last[8],
            last[9],
            last[10],
            last[11]
        ]

        result.append(candle)

    return result


def backtest_symbol(symbol):

    try:

        data = get_klines(
            symbol,
            "1h",
            1000
        )

    except Exception:

        return None

    if len(data) < 300:

        return None

    wins = 0
    losses = 0
    total_r = 0
    trades = 0

    equity = 0
    peak = 0
    max_drawdown = 0

    # Son ~700 mum üzerinde
    # basit walk-forward test.

    start = 250

    for i in range(
        start,
        len(data) - 12
    ):

        window = data[
            i - 200:i
        ]

        future = data[
            i:i + 12
        ]

        data_4h = aggregate_4h_from_1h(
            window
        )

        if len(data_4h) < 60:
            continue

        try:

            result = analyze_symbol(
                symbol,
                window,
                data_4h,
                "NEUTRAL"
            )

        except Exception:

            continue

        if result["signal"] not in (
            "LONG",
            "SHORT"
        ):

            continue

        entry = float(
            data[i][4]
        )

        stop = result["stop"]
        tp2 = result["tp2"]

        if not stop or not tp2:
            continue

        trades += 1

        outcome = None

        for candle in future:

            high = float(
                candle[2]
            )

            low = float(
                candle[3]
            )

            if result["signal"] == "LONG":

                if low <= stop:

                    outcome = -1
                    break

                if high >= tp2:

                    outcome = 2.5
                    break

            else:

                if high >= stop:

                    outcome = -1
                    break

                if low <= tp2:

                    outcome = 2.5
                    break

        if outcome is None:

            final_price = float(
                future[-1][4]
            )

            if result["signal"] == "LONG":

                risk = (
                    entry - stop
                )

                if risk > 0:

                    outcome = (
                        final_price
                        - entry
                    ) / risk

            else:

                risk = (
                    stop - entry
                )

                if risk > 0:

                    outcome = (
                        entry
                        - final_price
                    ) / risk

            if outcome is None:
                continue

            outcome = max(
                -1,
                min(
                    2.5,
                    outcome
                )
            )

        total_r += outcome

        equity += outcome

        peak = max(
            peak,
            equity
        )

        drawdown = (
            peak
            - equity
        )

        max_drawdown = max(
            max_drawdown,
            drawdown
        )

        if outcome > 0:

            wins += 1

        else:

            losses += 1

    if trades == 0:
        return None

    win_rate = (
        wins
        / trades
        * 100
    )

    return {

        "symbol": symbol.replace(
            "USDT",
            ""
        ),

        "trades": trades,

        "wins": wins,

        "losses": losses,

        "win_rate": win_rate,

        "total_r": total_r,

        "max_drawdown": max_drawdown
    }


# =========================================================
# MAIN
# =========================================================

def main():

    print()

    print("=" * 70)

    print(
        "             CRYPTO RESEARCH AGENT 4.0"
    )

    print("=" * 70)

    print()

    print(
        "PRICE ACTION + MULTI-TIMEFRAME "
        "+ MARKET REGIME"
    )

    print()

    results = []

    # =====================================================
    # BTC MARKET REGIME
    # =====================================================

    print(
        "BTC 4H piyasa rejimi hesaplanıyor..."
    )

    try:

        btc_4h_data = get_klines(
            "BTCUSDT",
            "4h"
        )

        btc_4h = timeframe_analysis(
            btc_4h_data
        )

        btc_regime = market_regime(
            btc_4h
        )

        print()

        print(
            f"BTC 4H TREND : "
            f"{btc_4h['trend']}"
        )

        print(
            f"BTC 4H RSI   : "
            f"{btc_4h['rsi']:.1f}"
        )

        print(
            f"BTC REGIME   : "
            f"{btc_regime}"
        )

    except Exception as e:

        print(
            f"BTC filtre hatasi: {e}"
        )

        btc_4h = None
        btc_regime = "NEUTRAL"

    # =====================================================
    # WATCHLIST
    # =====================================================

    print()

    print("=" * 70)

    print(
        "                    TAKIP LISTESI"
    )

    print("=" * 70)

    for symbol in WATCHLIST:

        try:

            data_1h = get_klines(
                symbol,
                "1h"
            )

            time.sleep(0.4)

            data_4h = get_klines(
                symbol,
                "4h"
            )

            result = analyze_symbol(
                symbol,
                data_1h,
                data_4h,
                btc_regime
            )

            results.append(
                result
            )

            print()

            print(
                f"{result['symbol']:5} "
                f"{result['signal']:6} "
                f"{result['quality']:2} "
                f"{result['score']:2} "
                f"1H:{result['trend_1h']:8} "
                f"4H:{result['trend_4h']:8}"
            )

            time.sleep(0.5)

        except Exception as e:

            print()

            print(
                f"{symbol} HATA: {e}"
            )

    # =====================================================
    # MARKET SCAN
    # =====================================================

    print()

    print("=" * 70)

    print(
        "                  PIYASA TARAMASI"
    )

    print("=" * 70)

    try:

        market_symbols = (
            get_market_symbols()
        )

        print()

        print(
            f"{len(market_symbols)} "
            f"likit USDT paritesi taraniyor..."
        )

        for symbol in market_symbols:

            if symbol in WATCHLIST:
                continue

            try:

                data_1h = get_klines(
                    symbol,
                    "1h"
                )

                time.sleep(0.35)

                data_4h = get_klines(
                    symbol,
                    "4h"
                )

                result = analyze_symbol(
                    symbol,
                    data_1h,
                    data_4h,
                    btc_regime
                )

                results.append(
                    result
                )

                time.sleep(0.5)

            except Exception:

                continue

    except Exception as e:

        print(
            f"Tarama hatasi: {e}"
        )

    # =====================================================
    # OPPORTUNITIES
    # =====================================================

    opportunities = [

        r for r in results

        if r["signal"] in (
            "LONG",
            "SHORT"
        )

        and r["entry_status"] != "KACTI"
    ]

    quality_rank = {
        "A+": 4,
        "A": 3,
        "B": 2,
        "C": 1,
        "-": 0
    }

    opportunities.sort(

        key=lambda x: (
            quality_rank.get(
                x["quality"],
                0
            ),
            x["score"],
            x["rr"],
            x["pa_long"]
            + x["pa_short"]
        ),

        reverse=True
    )

    print()

    print("=" * 70)

    print(
        "                    EN IYI FIRSATLAR"
    )

    print("=" * 70)

    if not opportunities:

        print()

        print(
            "SU ANDA KALITELI "
            "TRADE FIRSATI YOK."
        )

        print(
            "BEKLE."
        )

    else:

        for i, result in enumerate(
            opportunities[:10],
            start=1
        ):

            print()

            print(
                f"{i}. "
                f"{result['symbol']} "
                f"{result['signal']} "
                f"[{result['quality']}]"
            )

            print(
                f"   Skor        : "
                f"{result['score']}"
            )

            print(
                f"   Fiyat       : "
                f"{price_format(result['price'])}"
            )

            print(
                f"   Giris       : "
                f"{price_format(result['entry'])}"
            )

            print(
                f"   Stop        : "
                f"{price_format(result['stop'])}"
            )

            print(
                f"   TP1         : "
                f"{price_format(result['tp1'])}"
            )

            print(
                f"   TP2         : "
                f"{price_format(result['tp2'])}"
            )

            print(
                f"   R/R         : "
                f"{result['rr']:.2f}"
            )

            print(
                f"   RSI         : "
                f"{result['rsi']:.1f}"
            )

            print(
                f"   Hacim       : "
                f"{result['volume_ratio']:.2f}x"
            )

            print(
                f"   1H          : "
                f"{result['trend_1h']}"
            )

            print(
                f"   4H          : "
                f"{result['trend_4h']}"
            )

            print(
                f"   BTC Rejim   : "
                f"{result['btc_regime']}"
            )

            print(
                f"   PA Long     : "
                f"{result['pa_long']}"
            )

            print(
                f"   PA Short    : "
                f"{result['pa_short']}"
            )

            print(
                "   Neden:"
            )

            for reason in result[
                "reasons"
            ]:

                print(
                    f"   - {reason}"
                )

    # =====================================================
    # WATCHLIST SUMMARY
    # =====================================================

    print()

    print("=" * 70)

    print(
        "                    TAKIP OZETI"
    )

    print("=" * 70)

    for result in results:

        if (
            result["symbol"]
            + "USDT"
            in WATCHLIST
        ):

            print(

                f"{result['symbol']:6} "

                f"{result['signal']:6} "

                f"{result['quality']:2} "

                f"{result['score']:2} "

                f"1H:{result['trend_1h'][:3]} "

                f"4H:{result['trend_4h'][:3]}"
            )

    # =====================================================
    # BACKTEST
    # =====================================================

    print()

    print("=" * 70)

    print(
        "                     BACKTEST"
    )

    print("=" * 70)

    print()

    print(
        "Son ~1000 adet 1H mum "
        "uzerinde walk-forward test..."
    )

    backtest_results = []

    for symbol in WATCHLIST:

        print(
            f"Backtest: {symbol}"
        )

        try:

            result = backtest_symbol(
                symbol
            )

            if result:

                backtest_results.append(
                    result
                )

                print(

                    f"   Islem: "
                    f"{result['trades']} | "

                    f"Win: "
                    f"{result['win_rate']:.1f}% | "

                    f"R: "
                    f"{result['total_r']:.2f} | "

                    f"DD: "
                    f"{result['max_drawdown']:.2f}"
                )

        except Exception as e:

            print(
                f"   Backtest hata: {e}"
            )

        time.sleep(0.5)

    # =====================================================
    # BEST BACKTEST
    # =====================================================

    print()

    print("=" * 70)

    print(
        "                  BACKTEST SIRALAMASI"
    )

    print("=" * 70)

    backtest_results.sort(

        key=lambda x: (
            x["total_r"],
            x["win_rate"]
        ),

        reverse=True
    )

    for i, result in enumerate(
        backtest_results,
        start=1
    ):

        print()

        print(
            f"{i}. {result['symbol']} "
            f"| {result['trades']} islem "
            f"| Win {result['win_rate']:.1f}% "
            f"| R {result['total_r']:.2f} "
            f"| DD {result['max_drawdown']:.2f}"
        )

    # =====================================================
    # FINAL
    # =====================================================

    print()

    print("=" * 70)

    print(
        "                  ANALIZ TAMAMLANDI"
    )

    print("=" * 70)

    print()

    print(
        "NOT: Bu sistem otomatik trade acmaz."
    )

    print(
        "Sinyaller teknik analiz ve "
        "backtest amacli uretilir."
    )


if __name__ == "__main__":

    main()
