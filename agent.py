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

INTERVAL = "1h"
KLINE_LIMIT = 200

MIN_QUOTE_VOLUME = 5_000_000
SCAN_LIMIT = 40


def get_json(path, params=None, retries=3):
    if params:
        path += "?" + urllib.parse.urlencode(params)

    url = BASE_URL + path

    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "CryptoResearchAgent/1.0"
                }
            )

            with urllib.request.urlopen(req, timeout=15) as response:
                return json.loads(response.read().decode())

        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise e


def sma(values, period):
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def ema(values, period):
    if len(values) < period:
        return None

    multiplier = 2 / (period + 1)

    result = sum(values[:period]) / period

    for price in values[period:]:
        result = (price - result) * multiplier + result

    return result


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
        avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))


def true_ranges(highs, lows, closes):
    tr = []

    for i in range(1, len(closes)):
        value = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1])
        )

        tr.append(value)

    return tr


def atr(highs, lows, closes, period=14):
    tr = true_ranges(highs, lows, closes)

    if len(tr) < period:
        return None

    return sum(tr[-period:]) / period


def macd(values):
    if len(values) < 50:
        return None, None, None

    ema12 = []
    ema26 = []

    multiplier12 = 2 / 13
    multiplier26 = 2 / 27

    e12 = sum(values[:12]) / 12
    e26 = sum(values[:26]) / 26

    for price in values[12:]:
        e12 = (price - e12) * multiplier12 + e12
        ema12.append(e12)

    for price in values[26:]:
        e26 = (price - e26) * multiplier26 + e26

    length = min(len(ema12), len(ema26))

    macd_values = []

    for i in range(length):
        macd_values.append(
            ema12[-length + i] - ema26[-length + i]
        )

    if len(macd_values) < 9:
        return None, None, None

    signal = ema(macd_values, 9)

    return macd_values[-1], signal, macd_values[-1] - signal


def get_klines(symbol):
    return get_json(
        "/api/v3/klines",
        {
            "symbol": symbol,
            "interval": INTERVAL,
            "limit": KLINE_LIMIT
        }
    )


def parse_klines(data):
    opens = [float(x[1]) for x in data]
    highs = [float(x[2]) for x in data]
    lows = [float(x[3]) for x in data]
    closes = [float(x[4]) for x in data]
    volumes = [float(x[5]) for x in data]

    return opens, highs, lows, closes, volumes


def calculate_levels(highs, lows, closes, atr_value):
    recent_high = max(highs[-50:])
    recent_low = min(lows[-50:])

    price = closes[-1]

    supports = [x for x in lows[-50:] if x < price]
    resistances = [x for x in highs[-50:] if x > price]

    if supports:
        support = max(supports)
    else:
        support = price - atr_value * 2

    if resistances:
        resistance = min(resistances)
    else:
        resistance = price + atr_value * 2

    return support, resistance, recent_low, recent_high


def analyze(symbol, data):
    opens, highs, lows, closes, volumes = parse_klines(data)

    price = closes[-1]

    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)

    rsi14 = rsi(closes, 14)

    macd_value, macd_signal, macd_hist = macd(closes)

    atr14 = atr(highs, lows, closes, 14)

    volume_avg = sma(volumes[:-1], 20)

    if volume_avg:
        volume_ratio = volumes[-1] / volume_avg
    else:
        volume_ratio = 0

    support, resistance, recent_low, recent_high = calculate_levels(
        highs,
        lows,
        closes,
        atr14
    )

    score_long = 0
    score_short = 0

    long_reasons = []
    short_reasons = []

    # =========================
    # TREND
    # =========================

    if price > ema20:
        score_long += 1
        long_reasons.append("Fiyat EMA20 üzerinde")

    if ema20 > ema50:
        score_long += 1
        long_reasons.append("EMA20 > EMA50")

    if price < ema20:
        score_short += 1
        short_reasons.append("Fiyat EMA20 altında")

    if ema20 < ema50:
        score_short += 1
        short_reasons.append("EMA20 < EMA50")

    # =========================
    # RSI
    # =========================

    if 45 <= rsi14 <= 68:
        score_long += 1
        long_reasons.append("RSI long bölgesinde")

    if 32 <= rsi14 <= 55:
        score_short += 1
        short_reasons.append("RSI short bölgesinde")

    # =========================
    # MACD
    # =========================

    if macd_value is not None:

        if macd_hist > 0:
            score_long += 1
            long_reasons.append("MACD pozitif")

        if macd_hist < 0:
            score_short += 1
            short_reasons.append("MACD negatif")

    # =========================
    # VOLUME
    # =========================

    if volume_ratio >= 1.2:
        score_long += 1
        score_short += 1

        long_reasons.append("Hacim güçlü")
        short_reasons.append("Hacim güçlü")

    # =========================
    # SETUP CALCULATION
    # =========================

    long_entry = price
    long_stop = min(
        support - atr14 * 0.25,
        price - atr14 * 1.2
    )

    long_risk = long_entry - long_stop

    long_tp1 = long_entry + long_risk * 1.5
    long_tp2 = long_entry + long_risk * 2.5

    long_rr = (
        (long_tp2 - long_entry) / long_risk
        if long_risk > 0 else 0
    )

    short_entry = price

    short_stop = max(
        resistance + atr14 * 0.25,
        price + atr14 * 1.2
    )

    short_risk = short_stop - short_entry

    short_tp1 = short_entry - short_risk * 1.5
    short_tp2 = short_entry - short_risk * 2.5

    short_rr = (
        (short_entry - short_tp2) / short_risk
        if short_risk > 0 else 0
    )

    # =========================
    # SIGNAL
    # =========================

    if score_long >= 4 and long_rr >= 2:
        signal = "LONG"
        score = score_long
        entry = long_entry
        stop = long_stop
        tp1 = long_tp1
        tp2 = long_tp2
        rr = long_rr
        reasons = long_reasons

    elif score_short >= 4 and short_rr >= 2:
        signal = "SHORT"
        score = score_short
        entry = short_entry
        stop = short_stop
        tp1 = short_tp1
        tp2 = short_tp2
        rr = short_rr
        reasons = short_reasons

    else:
        signal = "BEKLE"

        if score_long >= score_short:
            score = score_long
            reasons = long_reasons
        else:
            score = score_short
            reasons = short_reasons

        entry = price
        stop = 0
        tp1 = 0
        tp2 = 0
        rr = 0

    confidence = min(95, 40 + score * 10)

    return {
        "symbol": symbol.replace("USDT", ""),
        "price": price,
        "ema20": ema20,
        "ema50": ema50,
        "rsi": rsi14,
        "macd": macd_value,
        "macd_hist": macd_hist,
        "volume_ratio": volume_ratio,
        "atr": atr14,
        "support": support,
        "resistance": resistance,
        "signal": signal,
        "score": score,
        "confidence": confidence,
        "entry": entry,
        "stop": stop,
        "tp1": tp1,
        "tp2": tp2,
        "rr": rr,
        "reasons": reasons
    }


def format_price(value):
    if value >= 100:
        return f"${value:,.2f}"

    if value >= 1:
        return f"${value:.4f}"

    if value >= 0.01:
        return f"${value:.6f}"

    return f"${value:.8f}"


def print_analysis(result):
    print()
    print("=" * 55)
    print(result["symbol"])
    print("=" * 55)

    print(f"Fiyat        : {format_price(result['price'])}")
    print(f"EMA20        : {format_price(result['ema20'])}")
    print(f"EMA50        : {format_price(result['ema50'])}")
    print(f"RSI14        : {result['rsi']:.2f}")

    if result["macd"] is not None:
        print(f"MACD         : {result['macd']:.8f}")
        print(f"MACD Hist    : {result['macd_hist']:.8f}")

    print(f"Hacim Orani  : {result['volume_ratio']:.2f}x")
    print(f"Destek       : {format_price(result['support'])}")
    print(f"Direnc       : {format_price(result['resistance'])}")

    print()
    print(f"Sinyal       : {result['signal']}")
    print(f"Skor         : {result['score']}/5")
    print(f"Guven        : %{result['confidence']:.0f}")

    if result["signal"] != "BEKLE":
        print()
        print(f"Giris        : {format_price(result['entry'])}")
        print(f"Stop         : {format_price(result['stop'])}")
        print(f"TP1          : {format_price(result['tp1'])}")
        print(f"TP2          : {format_price(result['tp2'])}")
        print(f"R/R          : {result['rr']:.2f}")

    if result["reasons"]:
        print()
        print("Nedenler:")

        for reason in result["reasons"]:
            print(f"- {reason}")


def get_market_symbols():
    data = get_json("/api/v3/ticker/24hr")

    symbols = []

    for item in data:

        symbol = item.get("symbol", "")

        if not symbol.endswith("USDT"):
            continue

        if not symbol.isalnum():
            continue

        try:
            quote_volume = float(item.get("quoteVolume", 0))
        except:
            continue

        if quote_volume < MIN_QUOTE_VOLUME:
            continue

        symbols.append(
            (
                symbol,
                quote_volume
            )
        )

    symbols.sort(
        key=lambda x: x[1],
        reverse=True
    )

    return [x[0] for x in symbols[:SCAN_LIMIT]]


def main():

    print()
    print("=" * 60)
    print("        CRYPTO RESEARCH AGENT")
    print("=" * 60)

    print()
    print("BINANCE 1H TECHNICAL ANALYSIS")
    print()

    results = []

    # =========================================
    # WATCHLIST
    # =========================================

    print("Takip listesi analiz ediliyor...")

    for symbol in WATCHLIST:

        try:

            data = get_klines(symbol)

            result = analyze(symbol, data)

            results.append(result)

            print_analysis(result)

            time.sleep(0.25)

        except Exception as e:

            print()
            print(symbol)
            print(f"VERI ALMA HATASI: {e}")

    # =========================================
    # MARKET SCAN
    # =========================================

    print()
    print()
    print("=" * 60)
    print("        PIYASA FIRSAT TARAMASI")
    print("=" * 60)

    try:

        market_symbols = get_market_symbols()

        print(
            f"{len(market_symbols)} likit USDT paritesi taranacak."
        )

        for symbol in market_symbols:

            if symbol in WATCHLIST:
                continue

            try:

                data = get_klines(symbol)

                result = analyze(symbol, data)

                results.append(result)

                time.sleep(0.25)

            except Exception:
                continue

    except Exception as e:

        print(f"Piyasa tarama hatasi: {e}")

    # =========================================
    # OPPORTUNITIES
    # =========================================

    opportunities = [
        r for r in results
        if r["signal"] in ("LONG", "SHORT")
    ]

    opportunities.sort(
        key=lambda x: (
            x["score"],
            x["rr"],
            x["confidence"]
        ),
        reverse=True
    )

    print()
    print()
    print("=" * 60)
    print("             EN IYI FIRSATLAR")
    print("=" * 60)

    if not opportunities:

        print()
        print("SU ANDA KALITELI TRADE FIRSATI YOK.")
        print("BEKLE.")

    else:

        for i, result in enumerate(
            opportunities[:10],
            start=1
        ):

            print()
            print(
                f"{i}. {result['symbol']} "
                f"{result['signal']}"
            )

            print(
                f"   Skor      : "
                f"{result['score']}/5"
            )

            print(
                f"   Guven     : "
                f"%{result['confidence']:.0f}"
            )

            print(
                f"   Giris     : "
                f"{format_price(result['entry'])}"
            )

            print(
                f"   Stop      : "
                f"{format_price(result['stop'])}"
            )

            print(
                f"   TP1       : "
                f"{format_price(result['tp1'])}"
            )

            print(
                f"   TP2       : "
                f"{format_price(result['tp2'])}"
            )

            print(
                f"   R/R       : "
                f"{result['rr']:.2f}"
            )

            print("   Neden:")

            for reason in result["reasons"]:
                print(f"   - {reason}")

    # =========================================
    # WATCHLIST SUMMARY
    # =========================================

    print()
    print()
    print("=" * 60)
    print("              TAKIP LISTESI")
    print("=" * 60)

    watch_results = [
        r for r in results
        if r["symbol"] + "USDT" in WATCHLIST
    ]

    for result in watch_results:

        print(
            f"{result['symbol']:6} "
            f"{result['signal']:6} "
            f"{result['score']}/5 "
            f"RSI:{result['rsi']:.1f}"
        )

    print()
    print("=" * 60)
    print("ANALIZ TAMAMLANDI")
    print("=" * 60)


if __name__ == "__main__":
    main()
