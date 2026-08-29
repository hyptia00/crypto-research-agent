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

BINANCE_URL = "https://api.binance.com/api/v3/klines"


def get_prices(symbol):
    params = urllib.parse.urlencode({
        "symbol": symbol,
        "interval": "1h",
        "limit": 200
    })

    url = BINANCE_URL + "?" + params

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Crypto-Research-Agent"
        }
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        data = json.loads(response.read().decode())

    return [float(candle[4]) for candle in data]


def ema(prices, period):
    multiplier = 2 / (period + 1)

    value = prices[0]

    for price in prices[1:]:
        value = (price - value) * multiplier + value

    return value


def rsi(prices, period=14):
    gains = []
    losses = []

    for i in range(1, len(prices)):
        change = prices[i] - prices[i - 1]

        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))


def analyze(symbol):
    prices = get_prices(symbol)

    price = prices[-1]

    ema20 = ema(prices, 20)
    ema50 = ema(prices, 50)

    current_rsi = rsi(prices)

    ema12 = ema(prices, 12)
    ema26 = ema(prices, 26)

    macd = ema12 - ema26

    score = 0

    # EMA trend
    if price > ema20:
        score += 1
    else:
        score -= 1

    if ema20 > ema50:
        score += 1
    else:
        score -= 1

    # RSI
    if current_rsi >= 55:
        score += 1
    elif current_rsi <= 45:
        score -= 1

    # MACD
    if macd > 0:
        score += 1
    else:
        score -= 1

    # Trend
    if price > ema20 and ema20 > ema50:
        trend = "YUKSELIS"
    elif price < ema20 and ema20 < ema50:
        trend = "DUSUS"
    else:
        trend = "KARARSIZ"

    # Momentum
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

    # Signal
    if score >= 3:
        signal = "AL"
    elif score <= -3:
        signal = "SAT"
    else:
        signal = "BEKLE"

    return {
        "symbol": symbol.replace("USDT", ""),
        "price": price,
        "ema20": ema20,
        "ema50": ema50,
        "rsi": current_rsi,
        "macd": macd,
        "trend": trend,
        "momentum": momentum,
        "score": score,
        "signal": signal
    }


print("=" * 55)
print("CRYPTO RESEARCH AGENT")
print("=" * 55)
print("BINANCE 1H TECHNICAL ANALYSIS")
print("=" * 55)

results = []

for symbol in COINS:

    try:
        result = analyze(symbol)
        results.append(result)

        print()
        print(result["symbol"])
        print("-" * 40)

        print(f"Fiyat: ${result['price']:,.6f}")
        print(f"EMA20: ${result['ema20']:,.6f}")
        print(f"EMA50: ${result['ema50']:,.6f}")
        print(f"RSI14: {result['rsi']:.2f}")
        print(f"MACD: {result['macd']:.6f}")

        print(f"Trend: {result['trend']}")
        print(f"Momentum: {result['momentum']}")

        print(f"SKOR: {result['score']}/4")
        print(f"SINYAL: {result['signal']}")

    except Exception as e:

        print()
        print(symbol.replace("USDT", ""))
        print(f"VERI ALMA HATASI: {e}")


print()
print("=" * 55)
print("SINYAL OZETI")
print("=" * 55)

for result in results:

    print(
        f"{result['symbol']:6} "
        f"{result['signal']:6} "
        f"Skor: {result['score']:>2}/4  "
        f"RSI: {result['rsi']:>5.1f}  "
        f"Trend: {result['trend']}"
    )

print("=" * 55)
