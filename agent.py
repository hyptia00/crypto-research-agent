import json
import urllib.request

COINS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "DOT": "polkadot",
    "NEAR": "near",
    "JUP": "jupiter-exchange-solana",
    "MOVR": "moonriver",
    "TNSR": "tensor"
}


def get_prices(coin_id):
    url = (
        f"https://api.coingecko.com/api/v3/coins/"
        f"{coin_id}/market_chart?vs_currency=usd&days=30"
    )

    with urllib.request.urlopen(url, timeout=20) as response:
        data = json.loads(response.read().decode())

    return [x[1] for x in data["prices"]]


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


def analyze(symbol, coin_id):
    prices = get_prices(coin_id)

    price = prices[-1]

    ema20 = ema(prices[-20:], 20)
    ema50 = ema(prices[-50:], 50)

    current_rsi = rsi(prices)

    ema12 = ema(prices[-12:], 12)
    ema26 = ema(prices[-26:], 26)
    macd = ema12 - ema26

    if price > ema20 and ema20 > ema50:
        trend = "YUKSELIS"
    elif price < ema20 and ema20 < ema50:
        trend = "DUSUS"
    else:
        trend = "KARARSIZ"

    if current_rsi >= 70:
        momentum = "ASIRI ALIM"
    elif current_rsi <= 30:
        momentum = "ASIRI SATIM"
    elif current_rsi < 45:
        momentum = "ZAYIF"
    elif current_rsi > 55:
        momentum = "GUCLU"
    else:
        momentum = "NOTR"

    if macd > 0:
        macd_signal = "POZITIF"
    else:
        macd_signal = "NEGATIF"

    print()
    print("=" * 45)
    print(symbol)
    print("=" * 45)
    print(f"Fiyat: ${price:,.4f}")
    print(f"EMA20: ${ema20:,.4f}")
    print(f"EMA50: ${ema50:,.4f}")
    print(f"RSI14: {current_rsi:.2f}")
    print(f"MACD: {macd:.6f}")
    print(f"Trend: {trend}")
    print(f"Momentum: {momentum}")
    print(f"MACD Durumu: {macd_signal}")


print("=" * 45)
print("CRYPTO RESEARCH AGENT")
print("=" * 45)

for symbol, coin_id in COINS.items():
    try:
        analyze(symbol, coin_id)
    except Exception as e:
        print()
        print(symbol)
        print("VERI ALMA HATASI:", e)
