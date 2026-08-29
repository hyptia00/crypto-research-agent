import json
import urllib.request

URL = "https://api.coingecko.com/api/v3/ping"

try:
    with urllib.request.urlopen(URL, timeout=15) as response:
        data = json.loads(response.read().decode("utf-8"))

    print("================================")
    print("CRYPTO RESEARCH AGENT")
    print("================================")
    print("CoinGecko bağlantısı başarılı.")
    print(data)

except Exception as e:
    print("VERİ ALMA HATASI:")
    print(e)
