# ============================================================
# CRYPTO RESEARCH AGENT
# MARKET DATA ENGINE
# ============================================================

import json
import time
import urllib.parse
import urllib.request
import urllib.error

from config import (
    QUOTE_ASSET,
    CORE_SYMBOLS,
    EXCLUDED_SYMBOLS,
    DISCOVERY_MAX_SYMBOLS,
    MIN_24H_QUOTE_VOLUME_USDT,
    MIN_PRICE_USDT,
    REQUEST_TIMEOUT,
    REQUEST_DELAY_SECONDS,
    MAX_RETRIES,
    CACHE_ENABLED,
    CACHE_SECONDS,
    KLINE_LIMIT_4H,
    KLINE_LIMIT_1H,
    KLINE_LIMIT_15M,
    KLINE_LIMIT_5M,
    KLINE_LIMIT_1M,
)


# ------------------------------------------------------------
# BINANCE ENDPOINTS
# ------------------------------------------------------------

SPOT_BASE_URL = "https://api.binance.com"

FUTURES_BASE_URL = "https://fapi.binance.com"


# ------------------------------------------------------------
# MEMORY CACHE
# ------------------------------------------------------------

_CACHE = {}


# ------------------------------------------------------------
# RATE LIMIT CONTROL
# ------------------------------------------------------------

_LAST_REQUEST_TIME = 0


def _respect_rate_limit():
    """
    Binance API istekleri arasında minimum bekleme.
    """

    global _LAST_REQUEST_TIME

    now = time.time()

    elapsed = now - _LAST_REQUEST_TIME

    if elapsed < REQUEST_DELAY_SECONDS:
        time.sleep(REQUEST_DELAY_SECONDS - elapsed)

    _LAST_REQUEST_TIME = time.time()


# ------------------------------------------------------------
# HTTP REQUEST
# ------------------------------------------------------------

def _request_json(url):
    """
    Binance API'den JSON veri alır.

    429 durumunda exponential backoff uygular.
    """

    cache_key = url

    if CACHE_ENABLED:
        cached = _CACHE.get(cache_key)

        if cached:
            timestamp, data = cached

            if time.time() - timestamp < CACHE_SECONDS:
                return data

    last_error = None

    for attempt in range(MAX_RETRIES):

        try:

            _respect_rate_limit()

            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "CryptoResearchAgent/2.0"
                }
            )

            with urllib.request.urlopen(
                request,
                timeout=REQUEST_TIMEOUT
            ) as response:

                raw = response.read().decode("utf-8")

                data = json.loads(raw)

                if CACHE_ENABLED:
                    _CACHE[cache_key] = (
                        time.time(),
                        data
                    )

                return data

        except urllib.error.HTTPError as e:

            last_error = e

            if e.code == 429:

                wait_time = min(
                    2 ** attempt,
                    10
                )

                time.sleep(wait_time)

                continue

            if e.code == 418:

                wait_time = min(
                    5 * (attempt + 1),
                    30
                )

                time.sleep(wait_time)

                continue

            raise

        except Exception as e:

            last_error = e

            wait_time = min(
                2 ** attempt,
                8
            )

            time.sleep(wait_time)

    raise RuntimeError(
        f"Binance veri alınamadı: {last_error}"
    )


# ------------------------------------------------------------
# SYMBOL NORMALIZATION
# ------------------------------------------------------------

def normalize_symbol(symbol):
    """
    BTC -> BTCUSDT
    BTCUSDT -> BTCUSDT
    """

    symbol = symbol.upper()

    if symbol.endswith(QUOTE_ASSET):
        return symbol

    return symbol + QUOTE_ASSET


# ------------------------------------------------------------
# KLINE LIMIT
# ------------------------------------------------------------

def get_kline_limit(timeframe):
    """
    Timeframe'e göre uygun candle sayısı.
    """

    limits = {
        "4h": KLINE_LIMIT_4H,
        "1h": KLINE_LIMIT_1H,
        "15m": KLINE_LIMIT_15M,
        "5m": KLINE_LIMIT_5M,
        "1m": KLINE_LIMIT_1M,
    }

    return limits.get(
        timeframe,
        300
    )


# ------------------------------------------------------------
# SPOT KLINES
# ------------------------------------------------------------

def get_spot_klines(
    symbol,
    timeframe="1h",
    limit=None
):
    """
    Binance Spot OHLCV verisi.

    Dönen yapı:

    [
        {
            "open_time": ...,
            "open": ...,
            "high": ...,
            "low": ...,
            "close": ...,
            "volume": ...,
            "close_time": ...
        }
    ]
    """

    symbol = normalize_symbol(symbol)

    if limit is None:
        limit = get_kline_limit(timeframe)

    params = urllib.parse.urlencode({
        "symbol": symbol,
        "interval": timeframe,
        "limit": limit,
    })

    url = (
        f"{SPOT_BASE_URL}/api/v3/klines?"
        f"{params}"
    )

    raw_data = _request_json(url)

    return _parse_klines(raw_data)


# ------------------------------------------------------------
# FUTURES KLINES
# ------------------------------------------------------------

def get_futures_klines(
    symbol,
    timeframe="1h",
    limit=None
):
    """
    Binance USDT-M Futures OHLCV verisi.
    """

    symbol = normalize_symbol(symbol)

    if limit is None:
        limit = get_kline_limit(timeframe)

    params = urllib.parse.urlencode({
        "symbol": symbol,
        "interval": timeframe,
        "limit": limit,
    })

    url = (
        f"{FUTURES_BASE_URL}/fapi/v1/klines?"
        f"{params}"
    )

    raw_data = _request_json(url)

    return _parse_klines(raw_data)


# ------------------------------------------------------------
# KLINE PARSER
# ------------------------------------------------------------

def _parse_klines(raw_data):
    """
    Binance'ın ham candle formatını
    sistemimizin standart formatına çevirir.
    """

    candles = []

    for row in raw_data:

        candles.append({
            "open_time": int(row[0]),

            "open": float(row[1]),

            "high": float(row[2]),

            "low": float(row[3]),

            "close": float(row[4]),

            "volume": float(row[5]),

            "close_time": int(row[6]),

            "quote_volume": float(row[7]),

            "trades": int(row[8]),

            "taker_buy_base": float(row[9]),

            "taker_buy_quote": float(row[10]),
        })

    return candles


# ------------------------------------------------------------
# CURRENT PRICE
# ------------------------------------------------------------

def get_price(symbol):

    symbol = normalize_symbol(symbol)

    params = urllib.parse.urlencode({
        "symbol": symbol
    })

    url = (
        f"{SPOT_BASE_URL}/api/v3/ticker/price?"
        f"{params}"
    )

    data = _request_json(url)

    return float(data["price"])


# ------------------------------------------------------------
# 24H TICKER
# ------------------------------------------------------------

def get_24h_ticker(symbol):

    symbol = normalize_symbol(symbol)

    params = urllib.parse.urlencode({
        "symbol": symbol
    })

    url = (
        f"{SPOT_BASE_URL}/api/v3/ticker/24hr?"
        f"{params}"
    )

    return _request_json(url)


# ------------------------------------------------------------
# ALL 24H TICKERS
# ------------------------------------------------------------

def get_all_24h_tickers():
    """
    Bütün Spot USDT marketlerinin 24h verisini
    tek API isteğinde alır.

    Bu özellikle 429 problemini azaltmak için önemli.
    """

    url = (
        f"{SPOT_BASE_URL}/api/v3/ticker/24hr"
    )

    return _request_json(url)


# ------------------------------------------------------------
# MARKET DISCOVERY
# ------------------------------------------------------------

def discover_symbols(
    max_symbols=None,
    min_volume=None
):
    """
    Piyasadaki likit USDT coinleri keşfeder.

    Ana coin listesine bağlı kalmaz.
    """

    if max_symbols is None:
        max_symbols = DISCOVERY_MAX_SYMBOLS

    if min_volume is None:
        min_volume = MIN_24H_QUOTE_VOLUME_USDT

    tickers = get_all_24h_tickers()

    candidates = []

    for ticker in tickers:

        symbol = ticker.get("symbol", "")

        if not symbol.endswith(QUOTE_ASSET):
            continue

        if symbol in EXCLUDED_SYMBOLS:
            continue

        try:

            price = float(
                ticker.get("lastPrice", 0)
            )

            quote_volume = float(
                ticker.get(
                    "quoteVolume",
                    0
                )
            )

        except (TypeError, ValueError):

            continue

        if price < MIN_PRICE_USDT:
            continue

        if quote_volume < min_volume:
            continue

        candidates.append({
            "symbol": symbol,
            "price": price,
            "quote_volume": quote_volume,
            "change_24h": float(
                ticker.get(
                    "priceChangePercent",
                    0
                )
            ),
        })

    # Hacme göre sırala
    candidates.sort(
        key=lambda x: x["quote_volume"],
        reverse=True
    )

    # Sadece sembolleri döndür
    return [
        item["symbol"]
        for item in candidates[:max_symbols]
    ]


# ------------------------------------------------------------
# CORE + DISCOVERED SYMBOLS
# ------------------------------------------------------------

def get_analysis_symbols():

    discovered = discover_symbols()

    result = []

    # Önce ana coinler
    for symbol in CORE_SYMBOLS:

        symbol = normalize_symbol(symbol)

        if symbol not in result:
            result.append(symbol)

    # Daha sonra keşfedilenler
    for symbol in discovered:

        if symbol not in result:
            result.append(symbol)

    return result


# ------------------------------------------------------------
# MARKET SNAPSHOT
# ------------------------------------------------------------

def get_market_snapshot(
    symbol,
    timeframe="1h",
    market="spot"
):
    """
    Tek coin için temel piyasa snapshot'ı.
    """

    symbol = normalize_symbol(symbol)

    if market.lower() == "futures":

        candles = get_futures_klines(
            symbol,
            timeframe
        )

    else:

        candles = get_spot_klines(
            symbol,
            timeframe
        )

    if not candles:
        raise RuntimeError(
            f"{symbol} için candle verisi yok."
        )

    last = candles[-1]

    return {
        "symbol": symbol,

        "timeframe": timeframe,

        "price": last["close"],

        "open": last["open"],

        "high": last["high"],

        "low": last["low"],

        "volume": last["volume"],

        "quote_volume": last["quote_volume"],

        "candles": candles,
    }


# ------------------------------------------------------------
# MULTI TIMEFRAME DATA
# ------------------------------------------------------------

def get_multi_timeframe_data(
    symbol,
    market="spot",
    timeframes=None
):
    """
    4H -> 1H -> 15M -> 5M -> 1M
    verilerini tek coin için toplar.

    İleride bütün strateji motorları
    bu fonksiyonu kullanacak.
    """

    if timeframes is None:

        timeframes = [
            "4h",
            "1h",
            "15m",
            "5m",
            "1m",
        ]

    result = {}

    for timeframe in timeframes:

        if market.lower() == "futures":

            result[timeframe] = get_futures_klines(
                symbol,
                timeframe
            )

        else:

            result[timeframe] = get_spot_klines(
                symbol,
                timeframe
            )

    return result


# ------------------------------------------------------------
# MARKET DATA HEALTH CHECK
# ------------------------------------------------------------

def health_check():

    try:

        data = _request_json(
            f"{SPOT_BASE_URL}/api/v3/ping"
        )

        return {
            "status": "OK",
            "message": "Binance bağlantısı başarılı.",
            "data": data,
        }

    except Exception as e:

        return {
            "status": "ERROR",
            "message": str(e),
        }


# ------------------------------------------------------------
# CACHE CONTROL
# ------------------------------------------------------------

def clear_cache():

    _CACHE.clear()


# ------------------------------------------------------------
# TEST
# ------------------------------------------------------------

if __name__ == "__main__":

    print("=" * 60)
    print("MARKET DATA ENGINE TEST")
    print("=" * 60)

    health = health_check()

    print()
    print("Binance bağlantısı:")
    print(health["status"])

    if health["status"] == "OK":

        print()
        print("BTC fiyatı:")

        try:

            btc = get_price("BTCUSDT")

            print(f"${btc:,.2f}")

        except Exception as e:

            print("HATA:", e)

        print()
        print("BTC 1H candle sayısı:")

        try:

            candles = get_spot_klines(
                "BTCUSDT",
                "1h",
                10
            )

            print(len(candles))

        except Exception as e:

            print("HATA:", e)

        print()
        print("Market discovery:")

        try:

            symbols = discover_symbols(
                max_symbols=10
            )

            print(
                ", ".join(symbols)
            )

        except Exception as e:

            print("HATA:", e)

    print()
    print("=" * 60)
    print("TEST TAMAMLANDI")
    print("=" * 60)
