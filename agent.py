import json
import urllib.request
import urllib.parse
import time

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
SCAN_LIMIT = 40
MIN_QUOTE_VOLUME = 5_000_000


# =========================================================
# API
# =========================================================

def get_json(path, params=None, retries=3):

    if params:
        path += "?" + urllib.parse.urlencode(params)

    url = BASE_URL + path

    for attempt in range(retries):

        try:

            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "CryptoResearchAgent/2.0"
                }
            )

            with urllib.request.urlopen(
                request,
                timeout=15
            ) as response:

                return json.loads(
                    response.read().decode()
                )

        except Exception as e:

            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise e


def get_klines(symbol, interval):

    return get_json(
        "/api/v3/klines",
        {
            "symbol": symbol,
            "interval": interval,
            "limit": KLINE_LIMIT
        }
    )


# =========================================================
# INDICATORS
# =========================================================

def ema(values, period):

    if len(values) < period:
        return None

    multiplier = 2 / (period + 1)

    result = sum(values[:period]) / period

    for price in values[period:]:
        result = (
            (price - result) * multiplier
            + result
        )

    return result


def sma(values, period):

    if len(values) < period:
        return None

    return sum(values[-period:]) / period


def rsi(values, period=14):

    if len(values) < period + 1:
        return None

    gains = []
    losses = []

    for i in range(1, len(values)):

        change = values[i] - values[i - 1]

        gains.append(max(change, 0))
        losses.append(max(-change, 0))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

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
        return 100

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))


def macd(values):

    if len(values) < 50:
        return None, None, None

    ema12_values = []
    ema26_values = []

    multiplier12 = 2 / 13
    multiplier26 = 2 / 27

    e12 = sum(values[:12]) / 12
    e26 = sum(values[:26]) / 26

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
            ema12_values[-length + i] - e26
        )

    if len(macd_values) < 9:
        return None, None, None

    signal = ema(macd_values, 9)

    if signal is None:
        return None, None, None

    histogram = macd_values[-1] - signal

    return macd_values[-1], signal, histogram


def atr(highs, lows, closes, period=14):

    if len(closes) < period + 1:
        return None

    ranges = []

    for i in range(1, len(closes)):

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

    return sum(ranges[-period:]) / period


# =========================================================
# DATA
# =========================================================

def parse_klines(data):

    opens = [float(x[1]) for x in data]
    highs = [float(x[2]) for x in data]
    lows = [float(x[3]) for x in data]
    closes = [float(x[4]) for x in data]
    volumes = [float(x[5]) for x in data]

    return (
        opens,
        highs,
        lows,
        closes,
        volumes
    )


# =========================================================
# TREND ANALYSIS
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

    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)

    rsi14 = rsi(closes, 14)

    macd_value, macd_signal, macd_hist = macd(
        closes
    )

    atr14 = atr(
        highs,
        lows,
        closes
    )

    if price > ema20 and ema20 > ema50:

        trend = "YUKSELIS"

    elif price < ema20 and ema20 < ema50:

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

    lows = info["lows"][-50:]
    highs = info["highs"][-50:]

    supports = [
        x for x in lows
        if x < price
    ]

    resistances = [
        x for x in highs
        if x > price
    ]

    if supports:
        support = max(supports)
    else:
        support = price - info["atr"] * 2

    if resistances:
        resistance = min(resistances)
    else:
        resistance = price + info["atr"] * 2

    return support, resistance


# =========================================================
# VOLUME
# =========================================================

def volume_ratio(info):

    volumes = info["volumes"]

    average = sma(
        volumes[:-1],
        20
    )

    if not average or average == 0:
        return 0

    return volumes[-1] / average


# =========================================================
# OPPORTUNITY ANALYSIS
# =========================================================

def analyze_symbol(symbol, data_1h, data_4h):

    one_h = timeframe_analysis(data_1h)
    four_h = timeframe_analysis(data_4h)

    price = one_h["price"]

    support, resistance = levels(one_h)

    vol_ratio = volume_ratio(one_h)

    long_score = 0
    short_score = 0

    long_reasons = []
    short_reasons = []

    # -----------------------------------------------------
    # 4H MARKET DIRECTION
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

    # -----------------------------------------------------
    # 1H TREND
    # -----------------------------------------------------

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
    # LONG SETUP
    # -----------------------------------------------------

    long_entry = price

    long_stop = min(
        support - one_h["atr"] * 0.25,
        price - one_h["atr"] * 1.2
    )

    long_risk = (
        long_entry - long_stop
    )

    long_tp1 = (
        long_entry
        + long_risk * 1.5
    )

    long_tp2 = (
        long_entry
        + long_risk * 2.5
    )

    long_rr = (
        (long_tp2 - long_entry)
        / long_risk
        if long_risk > 0
        else 0
    )

    # -----------------------------------------------------
    # SHORT SETUP
    # -----------------------------------------------------

    short_entry = price

    short_stop = max(
        resistance + one_h["atr"] * 0.25,
        price + one_h["atr"] * 1.2
    )

    short_risk = (
        short_stop - short_entry
    )

    short_tp1 = (
        short_entry
        - short_risk * 1.5
    )

    short_tp2 = (
        short_entry
        - short_risk * 2.5
    )

    short_rr = (
        (short_entry - short_tp2)
        / short_risk
        if short_risk > 0
        else 0
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

    if (
        long_score >= 5
        and four_h["trend"] == "YUKSELIS"
        and one_h["trend"] == "YUKSELIS"
        and long_rr >= 2
    ):

        signal = "LONG"

        score = long_score

        reasons = long_reasons

        entry = long_entry
        stop = long_stop
        tp1 = long_tp1
        tp2 = long_tp2
        rr = long_rr

    elif (
        short_score >= 5
        and four_h["trend"] == "DUSUS"
        and one_h["trend"] == "DUSUS"
        and short_rr >= 2
    ):

        signal = "SHORT"

        score = short_score

        reasons = short_reasons

        entry = short_entry
        stop = short_stop
        tp1 = short_tp1
        tp2 = short_tp2
        rr = short_rr

    # -----------------------------------------------------
    # SETUP QUALITY
    # -----------------------------------------------------

    if signal == "LONG" or signal == "SHORT":

        if score >= 7:
            quality = "A"

        elif score >= 6:
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

        "entry_status": entry_status,

        "reasons": reasons
    }


# =========================================================
# PRICE FORMAT
# =========================================================

def price_format(value):

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
# MAIN
# =========================================================

def main():

    print()
    print("=" * 60)
    print("          CRYPTO RESEARCH AGENT")
    print("=" * 60)

    print()
    print("4H + 1H MULTI-TIMEFRAME ANALYSIS")
    print()

    results = []

    # =====================================================
    # BTC MARKET FILTER
    # =====================================================

    print("BTC 4H piyasa filtresi hesaplanıyor...")

    try:

        btc_4h_data = get_klines(
            "BTCUSDT",
            "4h"
        )

        btc_4h = timeframe_analysis(
            btc_4h_data
        )

        print()
        print(
            f"BTC 4H TREND: "
            f"{btc_4h['trend']}"
        )

        print(
            f"BTC 4H RSI: "
            f"{btc_4h['rsi']:.1f}"
        )

    except Exception as e:

        print(
            f"BTC filtre hatasi: {e}"
        )

        btc_4h = None

    # =====================================================
    # WATCHLIST
    # =====================================================

    print()
    print("=" * 60)
    print("              TAKIP LISTESI")
    print("=" * 60)

    for symbol in WATCHLIST:

        try:

            data_1h = get_klines(
                symbol,
                "1h"
            )

            data_4h = get_klines(
                symbol,
                "4h"
            )

            result = analyze_symbol(
                symbol,
                data_1h,
                data_4h
            )

            results.append(result)

            print()
            print(
                f"{result['symbol']} "
                f"{result['signal']} "
                f"{result['score']}/7 "
                f"1H:{result['trend_1h']} "
                f"4H:{result['trend_4h']}"
            )

            time.sleep(0.25)

        except Exception as e:

            print()
            print(
                f"{symbol} HATA: {e}"
            )

    # =====================================================
    # MARKET SCAN
    # =====================================================

    print()
    print("=" * 60)
    print("           PIYASA TARAMASI")
    print("=" * 60)

    try:

        market_symbols = get_market_symbols()

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

                data_4h = get_klines(
                    symbol,
                    "4h"
                )

                result = analyze_symbol(
                    symbol,
                    data_1h,
                    data_4h
                )

                results.append(result)

                time.sleep(0.25)

            except Exception:

                continue

    except Exception as e:

        print(
            f"Tarama hatasi: {e}"
        )

    # =====================================================
    # BTC FILTER
    # =====================================================

    if btc_4h:

        btc_trend = btc_4h["trend"]

        for result in results:

            if result["signal"] == "LONG":

                if btc_trend == "DUSUS":

                    result["signal"] = "BEKLE"
                    result["quality"] = "-"
                    result["entry_status"] = "BTC FILTRELEDI"

            elif result["signal"] == "SHORT":

                if btc_trend == "YUKSELIS":

                    result["signal"] = "BEKLE"
                    result["quality"] = "-"
                    result["entry_status"] = "BTC FILTRELEDI"

    # =====================================================
    # BEST OPPORTUNITIES
    # =====================================================

    opportunities = [
        r for r in results
        if r["signal"] in (
            "LONG",
            "SHORT"
        )
        and r["entry_status"] != "KACTI"
    ]

    opportunities.sort(
        key=lambda x: (
            x["quality"],
            x["score"],
            x["rr"]
        ),
        reverse=True
    )

    print()
    print()
    print("=" * 60)
    print("              EN IYI FIRSATLAR")
    print("=" * 60)

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
                f"{result['signal']}"
            )

            print(
                f"   Kalite : "
                f"{result['quality']}"
            )

            print(
                f"   Skor   : "
                f"{result['score']}/7"
            )

            print(
                f"   Fiyat  : "
                f"{price_format(result['price'])}"
            )

            print(
                f"   Giris  : "
                f"{price_format(result['entry'])}"
            )

            print(
                f"   Stop   : "
                f"{price_format(result['stop'])}"
            )

            print(
                f"   TP1    : "
                f"{price_format(result['tp1'])}"
            )

            print(
                f"   TP2    : "
                f"{price_format(result['tp2'])}"
            )

            print(
                f"   R/R    : "
                f"{result['rr']:.2f}"
            )

            print(
                f"   RSI    : "
                f"{result['rsi']:.1f}"
            )

            print(
                f"   Hacim  : "
                f"{result['volume_ratio']:.2f}x"
            )

            print(
                f"   1H     : "
                f"{result['trend_1h']}"
            )

            print(
                f"   4H     : "
                f"{result['trend_4h']}"
            )

            print(
                "   Neden:"
            )

            for reason in result["reasons"]:

                print(
                    f"   - {reason}"
                )

    # =====================================================
    # WATCHLIST SUMMARY
    # =====================================================

    print()
    print()
    print("=" * 60)
    print("             TAKIP OZETI")
    print("=" * 60)

    for result in results:

        if (
            result["symbol"] + "USDT"
            in WATCHLIST
        ):

            print(
                f"{result['symbol']:6} "
                f"{result['signal']:6} "
                f"{result['score']}/7 "
                f"1H:{result['trend_1h'][:3]} "
                f"4H:{result['trend_4h'][:3]}"
            )

    print()
    print("=" * 60)
    print("             ANALIZ TAMAMLANDI")
    print("=" * 60)


if __name__ == "__main__":
    main()
