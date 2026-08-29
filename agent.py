import json
import urllib.request
import urllib.parse

COINS = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "DOTUSDT",
    "NEARUSDT",
    "JUPUSDT",
    "MOVRUSDT",
    "TNSRUSDT"
]

BINANCE_URL = "https://data-api.binance.vision/api/v3/klines"


def get_candles(symbol):
    params = urllib.parse.urlencode({
        "symbol": symbol,
        "interval": "1h",
        "limit": 200
    })

    url = BINANCE_URL + "?" + params

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Crypto-Research-Agent"}
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        data = json.loads(response.read().decode())

    candles = []

    for c in data:
        candles.append({
            "open": float(c[1]),
            "high": float(c[2]),
            "low": float(c[3]),
            "close": float(c[4]),
            "volume": float(c[5])
        })

    return candles


def ema(values, period):
    multiplier = 2 / (period + 1)
    value = values[0]

    for price in values[1:]:
        value = (price - value) * multiplier + value

    return value


def ema_series(values, period):
    result = []
    multiplier = 2 / (period + 1)
    value = values[0]

    result.append(value)

    for price in values[1:]:
        value = (price - value) * multiplier + value
        result.append(value)

    return result


def rsi(values, period=14):
    gains = []
    losses = []

    for i in range(1, len(values)):
        change = values[i] - values[i - 1]

        gains.append(max(change, 0))
        losses.append(max(-change, 0))

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))


def macd(values):
    ema12 = ema_series(values, 12)
    ema26 = ema_series(values, 26)

    macd_line = []

    for i in range(len(values)):
        macd_line.append(ema12[i] - ema26[i])

    signal_series = ema_series(macd_line, 9)

    return macd_line[-1], signal_series[-1]


def atr(candles, period=14):
    true_ranges = []

    for i in range(1, len(candles)):
        high = candles[i]["high"]
        low = candles[i]["low"]
        previous_close = candles[i - 1]["close"]

        tr = max(
            high - low,
            abs(high - previous_close),
            abs(low - previous_close)
        )

        true_ranges.append(tr)

    return sum(true_ranges[-period:]) / period


def volume_ratio(candles, period=20):
    current_volume = candles[-1]["volume"]

    previous_volumes = [
        candle["volume"]
        for candle in candles[-period-1:-1]
    ]

    average_volume = sum(previous_volumes) / len(previous_volumes)

    if average_volume == 0:
        return 1

    return current_volume / average_volume


def support_resistance(candles, period=50):
    recent = candles[-period:]

    support = min(c["low"] for c in recent)
    resistance = max(c["high"] for c in recent)

    return support, resistance


def analyze(symbol):
    candles = get_candles(symbol)

    closes = [c["close"] for c in candles]

    price = closes[-1]

    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)

    current_rsi = rsi(closes)

    macd_value, macd_signal = macd(closes)

    current_atr = atr(candles)

    vol_ratio = volume_ratio(candles)

    support, resistance = support_resistance(candles)

    score = 0

    reasons = []

    # EMA TREND
    if price > ema20:
        score += 1
        reasons.append("Fiyat EMA20 ustunde")
    else:
        score -= 1
        reasons.append("Fiyat EMA20 altinda")

    if ema20 > ema50:
        score += 1
        reasons.append("EMA20 EMA50 ustunde")
    else:
        score -= 1
        reasons.append("EMA20 EMA50 altinda")

    # RSI
    if 50 <= current_rsi <= 70:
        score += 1
        reasons.append("RSI pozitif")
    elif current_rsi < 35:
        score += 1
        reasons.append("RSI asiri satima yakin")
    elif current_rsi > 70:
        score -= 1
        reasons.append("RSI asiri alim")
    elif current_rsi < 45:
        score -= 1
        reasons.append("RSI zayif")

    # MACD
    if macd_value > macd_signal:
        score += 1
        reasons.append("MACD pozitif")
    else:
        score -= 1
        reasons.append("MACD negatif")

    # VOLUME
    if vol_ratio >= 1.5:
        if score > 0:
            score += 1
            reasons.append("Yuksek hacim")
        elif score < 0:
            score -= 1
            reasons.append("Yuksek satis hacmi")
        else:
            reasons.append("Yuksek hacim")
    else:
        reasons.append("Hacim normal")

    # TREND
    if price > ema20 and ema20 > ema50:
        trend = "YUKSELIS"
    elif price < ema20 and ema20 < ema50:
        trend = "DUSUS"
    else:
        trend = "KARARSIZ"

    # MOMENTUM
    if current_rsi >= 70:
        momentum = "ASIRI ALIM"
    elif current_rsi <= 30:
        momentum = "ASIRI SATIM"
    elif current_rsi >= 55:
        momentum = "GUCLU"
    elif current_rsi <= 45:
        momentum = "ZAYIF"
    else:
        momentum = "NOTR"

    # SUPPORT DISTANCE
    support_distance = ((price - support) / price) * 100

    # RESISTANCE DISTANCE
    resistance_distance = ((resistance - price) / price) * 100

    # SIGNAL
    if score >= 4:
        signal = "AL"
    elif score <= -4:
        signal = "SAT"
    else:
        signal = "BEKLE"

    # HEURISTIC CONFIDENCE
    confidence = int(min(95, 50 + abs(score) * 10))

    # RISK / REWARD
    long_stop = support - current_atr
    long_target = resistance

    if price > long_stop:
        long_risk = price - long_stop
        long_reward = long_target - price

        if long_risk > 0:
            long_rr = long_reward / long_risk
        else:
            long_rr = 0
    else:
        long_rr = 0

    return {
        "symbol": symbol.replace("USDT", ""),
        "price": price,
        "ema20": ema20,
        "ema50": ema50,
        "rsi": current_rsi,
        "macd": macd_value,
        "macd_signal": macd_signal,
        "atr": current_atr,
        "volume_ratio": vol_ratio,
        "support": support,
        "resistance": resistance,
        "support_distance": support_distance,
        "resistance_distance": resistance_distance,
        "trend": trend,
        "momentum": momentum,
        "score": score,
        "signal": signal,
        "confidence": confidence,
        "long_rr": long_rr,
        "reasons": reasons
    }


print("=" * 60)
print("CRYPTO RESEARCH AGENT")
print("=" * 60)
print("BINANCE 1H MULTI-FACTOR ANALYSIS")
print("=" * 60)

results = []

for symbol in COINS:

    try:
        result = analyze(symbol)
        results.append(result)

        print()
        print("=" * 60)
        print(result["symbol"])
        print("=" * 60)

        print(f"Fiyat       : ${result['price']:,.6f}")
        print(f"EMA20       : ${result['ema20']:,.6f}")
        print(f"EMA50       : ${result['ema50']:,.6f}")
        print(f"RSI14       : {result['rsi']:.2f}")
        print(f"MACD        : {result['macd']:.6f}")
        print(f"MACD Signal : {result['macd_signal']:.6f}")

        print(f"Hacim Orani : {result['volume_ratio']:.2f}x")
        print(f"ATR14       : ${result['atr']:,.6f}")

        print(f"Destek      : ${result['support']:,.6f}")
        print(f"Direnc      : ${result['resistance']:,.6f}")

        print(f"Trend       : {result['trend']}")
        print(f"Momentum    : {result['momentum']}")

        print(f"Skor        : {result['score']}/5")
        print(f"Sinyal      : {result['signal']}")
        print(f"Guven       : %{result['confidence']}")
        print(f"Long R/R    : {result['long_rr']:.2f}")

        print()
        print("Nedenler:")

        for reason in result["reasons"]:
            print(f"- {reason}")

    except Exception as e:

        print()
        print(symbol.replace("USDT", ""))
        print(f"VERI ALMA HATASI: {e}")


print()
print("=" * 60)
print("SINYAL OZETI")
print("=" * 60)

for result in results:

    print(
        f"{result['symbol']:6} "
        f"{result['signal']:6} "
        f"Skor: {result['score']:>2}/5  "
        f"RSI: {result['rsi']:>5.1f}  "
        f"Trend: {result['trend']:9}  "
        f"Guven: %{result['confidence']}"
    )

print("=" * 60)
