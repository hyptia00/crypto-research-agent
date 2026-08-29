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

try:
    request = urllib.request.Request(
        URL,
        headers={"User-Agent": "Crypto-Research-Agent/1.0"}
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        data = json.loads(response.read().decode("utf-8"))

    print("=" * 60)
    print("CRYPTO RESEARCH AGENT")
    print("=" * 60)
    print()

    names = {
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

    for coin_id, symbol in names.items():
        coin = data.get(coin_id, {})

        price = coin.get("usd")
        change = coin.get("usd_24h_change")
        volume = coin.get("usd_24h_vol")
        market_cap = coin.get("usd_market_cap")

        print(f"{symbol}")
        print(f"  Fiyat: ${price:,.2f}")
        print(f"  24s değişim: {change:.2f}%")
        print(f"  24s hacim: ${volume:,.0f}")
        print(f"  Piyasa değeri: ${market_cap:,.0f}")
        print()

    print("=" * 60)
    print("Araştırma tamamlandı.")
    print("=" * 60)

except Exception as e:
    print("VERİ ALMA HATASI:")
    print(e)
