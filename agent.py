import json
import urllib.request

COINS = (
    "bitcoin,ethereum,solana,binancecoin,ripple,"
    "jupiter-exchange-solana,moonriver,tensor,near,polkadot"
)

URL = (
    "https://api.coingecko.com/api/v3/simple/price"
    "?ids=" + COINS +
    "&vs_currencies=usd"
    "&include_24hr_change=true"
    "&include_24hr_vol=true"
    "&include_market_cap=true"
)

NAMES = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL",
    "binancecoin": "BNB",
    "ripple": "XRP",
    "jupiter-exchange-solana": "JUP",
    "moonriver": "MOVR",
    "tensor": "TNSR",
    "near": "NEAR",
    "polkadot": "DOT"
}


def get_data():
    request = urllib.request.Request(
        URL,
        headers={"User-Agent": "Crypto-Research-Agent/1.0"}
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


try:
    data = get_data()

    coins = []

    for coin_id, symbol in NAMES.items():

        coin = data.get(coin_id)

        if not coin:
            continue

        price = coin.get("usd", 0)
        change = coin.get("usd_24h_change", 0)
        volume = coin.get("usd_24h_vol", 0)
        market_cap = coin.get("usd_market_cap", 0)

        coins.append({
            "symbol": symbol,
            "price": price,
            "change": change,
            "volume": volume,
            "market_cap": market_cap
        })

    # 24 saatlik değişime göre sırala
    by_change = sorted(
        coins,
        key=lambda x: x["change"],
        reverse=True
    )

    # Hacme göre sırala
    by_volume = sorted(
        coins,
        key=lambda x: x["volume"],
        reverse=True
    )

    average_change = sum(
        coin["change"] for coin in coins
    ) / len(coins)

    print("=" * 60)
    print("CRYPTO RESEARCH AGENT")
    print("=" * 60)

    print("\n📊 24 SAATLİK PERFORMANS")
    print("-" * 60)

    for rank, coin in enumerate(by_change, 1):

        change = coin["change"]

        if change >= 3:
            signal = "GÜÇLÜ POZİTİF"
        elif change >= 0:
            signal = "POZİTİF"
        elif change > -3:
            signal = "NEGATİF"
        else:
            signal = "GÜÇLÜ NEGATİF"

        print(
            f"{rank:2}. {coin['symbol']:5} "
            f"{change:+7.2f}%   "
            f"${coin['price']:,.4f}   "
            f"{signal}"
        )

    print("\n💰 HACİM SIRALAMASI")
    print("-" * 60)

    for rank, coin in enumerate(by_volume, 1):
        print(
            f"{rank:2}. {coin['symbol']:5} "
            f"${coin['volume']:,.0f}"
        )

    print("\n📈 PİYASA ÖZETİ")
    print("-" * 60)

    print(f"İzlenen coin sayısı : {len(coins)}")
    print(f"Ortalama değişim    : {average_change:+.2f}%")

    strongest = by_change[0]
    weakest = by_change[-1]
    highest_volume = by_volume[0]

    print(
        f"En güçlü coin      : "
        f"{strongest['symbol']} ({strongest['change']:+.2f}%)"
    )

    print(
        f"En zayıf coin       : "
        f"{weakest['symbol']} ({weakest['change']:+.2f}%)"
    )

    print(
        f"En yüksek hacim     : "
        f"{highest_volume['symbol']}"
    )

    print("\n🧠 İLK ANALİZ")

    if average_change > 2:
        print("Piyasa genel olarak güçlü pozitif momentum gösteriyor.")
    elif average_change > 0:
        print("Piyasa genel olarak pozitif bölgede.")
    elif average_change > -2:
        print("Piyasa genel olarak hafif negatif bölgede.")
    else:
        print("Piyasa genel olarak güçlü negatif momentum gösteriyor.")

    print("\n" + "=" * 60)
    print("Araştırma tamamlandı.")
    print("=" * 60)


except Exception as e:

    print("=" * 60)
    print("VERİ ALMA HATASI")
    print("=" * 60)

    print(e)
