# ============================================================
# MARKET DATA ENGINE
# ============================================================

import time
import requests
import pandas as pd


# ============================================================
# BINANCE ENDPOINTS
# ============================================================

# Public Spot market data
SPOT_BASE_URL = "https://data-api.binance.vision"

# Binance Spot API fallback
SPOT_FALLBACK_URLS = [
    "https://api1.binance.com",
    "https://api2.binance.com",
    "https://api3.binance.com",
    "https://api4.binance.com",
]

# Futures market data
FUTURES_BASE_URL = "https://fapi.binance.com"


KLINE_ENDPOINT = "/api/v3/klines"
TICKER_ENDPOINT = "/api/v3/ticker/24hr"

FUTURES_KLINE_ENDPOINT = "/fapi/v1/klines"


# ============================================================
# SESSION
# ============================================================

SESSION = requests.Session()

SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 "
        "(Crypto Research Agent)"
    ),
    "Accept": "application/json",
})


# ============================================================
# HTTP
# ============================================================

def _get_url(
    base_url,
    endpoint,
    params=None,
    timeout=15,
):
    response = SESSION.get(
        base_url + endpoint,
        params=params,
        timeout=timeout,
    )

    response.raise_for_status()

    return response.json()


def _get_spot(
    endpoint,
    params=None,
    timeout=15,
):
    """
    Public Spot market data.

    Önce data-api.binance.vision kullanılır.
    451 / bağlantı problemi halinde Binance
    alternatif API endpointleri denenir.
    """

    urls = [
        SPOT_BASE_URL,
        *SPOT_FALLBACK_URLS,
    ]

    last_error = None

    for base_url in urls:

        try:

            return _get_url(
                base_url,
                endpoint,
                params=params,
                timeout=timeout,
            )

        except Exception as exc:

            last_error = exc

    raise last_error


def _get_futures(
    endpoint,
    params=None,
    timeout=15,
):
    """
    Binance Futures public market data.
    """

    return _get_url(
        FUTURES_BASE_URL,
        endpoint,
        params=params,
        timeout=timeout,
    )


# ============================================================
# KLINE PARSER
# ============================================================

def _parse_klines(
    raw,
):
    if not raw:
        return pd.DataFrame()

    columns = [
        "open_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_volume",
        "trades",
        "taker_buy_base",
        "taker_buy_quote",
        "ignore",
    ]

    df = pd.DataFrame(
        raw,
        columns=columns,
    )

    # --------------------------------------------------------
    # NUMERIC
    # --------------------------------------------------------

    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "quote_volume",
        "trades",
        "taker_buy_base",
        "taker_buy_quote",
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    # --------------------------------------------------------
    # TIME
    # --------------------------------------------------------

    df["open_time"] = pd.to_datetime(
        df["open_time"],
        unit="ms",
        utc=True,
    )

    df["close_time"] = pd.to_datetime(
        df["close_time"],
        unit="ms",
        utc=True,
    )

    # --------------------------------------------------------
    # REMOVE INVALID ROWS
    # --------------------------------------------------------

    df = df.dropna(
        subset=[
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]
    )

    # --------------------------------------------------------
    # INDEX
    # --------------------------------------------------------

    df = df.set_index(
        "open_time"
    )

    return df


# ============================================================
# SPOT KLINES
# ============================================================

def get_klines(
    symbol,
    interval,
    limit=200,
):
    """
    Binance Spot OHLCV verisi.
    """

    symbol = str(
        symbol
    ).upper()

    raw = _get_spot(
        KLINE_ENDPOINT,
        {
            "symbol": symbol,
            "interval": interval,
            "limit": int(limit),
        },
    )

    return _parse_klines(
        raw
    )


# ============================================================
# FUTURES KLINES
# ============================================================

def get_futures_klines(
    symbol,
    interval,
    limit=200,
):
    """
    Binance USDT-M Futures OHLCV verisi.
    """

    symbol = str(
        symbol
    ).upper()

    raw = _get_futures(
        FUTURES_KLINE_ENDPOINT,
        {
            "symbol": symbol,
            "interval": interval,
            "limit": int(limit),
        },
    )

    return _parse_klines(
        raw
    )


# ============================================================
# MULTI TIMEFRAME SPOT DATA
# ============================================================

def get_multi_timeframe_data(
    symbol,
    timeframes=None,
    limit=200,
):
    """
    Spot market için çoklu zaman dilimi.

    Dönen yapı:

        {
            "4h": DataFrame,
            "1h": DataFrame,
            "15m": DataFrame,
            "5m": DataFrame,
            "1m": DataFrame
        }
    """

    if timeframes is None:

        timeframes = [
            "4h",
            "1h",
            "15m",
            "5m",
            "1m",
        ]

    data = {}

    for timeframe in timeframes:

        try:

            df = get_klines(
                symbol,
                timeframe,
                limit,
            )

            data[timeframe] = df

            if df.empty:

                print(
                    f"DATA WARNING "
                    f"{symbol} "
                    f"{timeframe}: "
                    f"empty dataframe"
                )

        except Exception as exc:

            print(
                f"DATA ERROR "
                f"{symbol} "
                f"{timeframe}: "
                f"{exc}"
            )

            data[timeframe] = (
                pd.DataFrame()
            )

        # API rate limit için küçük bekleme
        time.sleep(0.10)

    return data


# ============================================================
# MULTI TIMEFRAME FUTURES DATA
# ============================================================

def get_multi_timeframe_futures_data(
    symbol,
    timeframes=None,
    limit=200,
):
    """
    Futures için çoklu zaman dilimi.
    """

    if timeframes is None:

        timeframes = [
            "4h",
            "1h",
            "15m",
            "5m",
            "1m",
        ]

    data = {}

    for timeframe in timeframes:

        try:

            df = get_futures_klines(
                symbol,
                timeframe,
                limit,
            )

            data[timeframe] = df

            if df.empty:

                print(
                    f"FUTURES DATA WARNING "
                    f"{symbol} "
                    f"{timeframe}: "
                    f"empty dataframe"
                )

        except Exception as exc:

            print(
                f"FUTURES DATA ERROR "
                f"{symbol} "
                f"{timeframe}: "
                f"{exc}"
            )

            data[timeframe] = (
                pd.DataFrame()
            )

        time.sleep(0.10)

    return data


# ============================================================
# PRICE
# ============================================================

def get_price(
    symbol,
):
    """
    Spot son fiyat.
    """

    symbol = str(
        symbol
    ).upper()

    data = _get_spot(
        TICKER_ENDPOINT,
        {
            "symbol": symbol,
        },
    )

    return float(
        data["lastPrice"]
    )


# ============================================================
# FUTURES PRICE
# ============================================================

def get_futures_price(
    symbol,
):
    """
    Futures son fiyat.
    """

    symbol = str(
        symbol
    ).upper()

    data = _get_futures(
        "/fapi/v1/ticker/price",
        {
            "symbol": symbol,
        },
    )

    return float(
        data["price"]
    )


# ============================================================
# ALL USDT SPOT MARKETS
# ============================================================

def get_usdt_tickers():
    """
    Binance Spot üzerindeki USDT marketlerini döndürür.
    """

    raw = _get_spot(
        TICKER_ENDPOINT
    )

    if not raw:
        return []

    return [
        ticker
        for ticker in raw
        if str(
            ticker.get(
                "symbol",
                "",
            )
        ).upper().endswith(
            "USDT"
        )
    ]


# ============================================================
# DISCOVER MARKETS
# ============================================================

def discover_usdt_markets(
    min_volume_usdt=10_000_000,
    limit=50,
):
    """
    Yüksek hacimli USDT marketlerini keşfeder.

    Bu fonksiyon işlem sinyali üretmez.
    """

    tickers = get_usdt_tickers()

    candidates = []

    for ticker in tickers:

        symbol = str(
            ticker.get(
                "symbol",
                "",
            )
        ).upper()

        if not symbol.endswith(
            "USDT"
        ):
            continue

        try:

            volume = float(
                ticker.get(
                    "quoteVolume",
                    0,
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            continue

        if volume < min_volume_usdt:
            continue

        try:

            price = float(
                ticker.get(
                    "lastPrice",
                    0,
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            price = 0.0

        try:

            change = float(
                ticker.get(
                    "priceChangePercent",
                    0,
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            change = 0.0

        candidates.append({

            "symbol":
                symbol,

            "price":
                price,

            "price_change_percent":
                change,

            "quote_volume":
                volume,

        })

    # --------------------------------------------------------
    # RANK
    # --------------------------------------------------------

    candidates.sort(
        key=lambda x:
            x["quote_volume"],
        reverse=True,
    )

    return candidates[
        :int(limit)
    ]


# ============================================================
# COMPATIBILITY
# ============================================================

def get_market_data(
    symbol,
    timeframe="15m",
    limit=200,
):
    """
    Eski modüllerle uyumluluk.
    """

    return get_klines(
        symbol,
        timeframe,
        limit,
    )


def fetch_ohlcv(
    symbol,
    timeframe="15m",
    limit=200,
):
    """
    Eski modüllerle uyumluluk.
    """

    return get_klines(
        symbol,
        timeframe,
        limit,
    )


# ============================================================
# GENERIC DATA LOADER
# ============================================================

def load_market_data(
    symbol,
    limit=200,
):
    """
    Hem Spot hem Futures verisini tek
    yapı altında hazırlar.

    Stratejiler gerektiğinde ilgili
    piyasayı seçebilir.
    """

    return {
        "spot": get_multi_timeframe_data(
            symbol,
            limit=limit,
        ),

        "futures": get_multi_timeframe_futures_data(
            symbol,
            limit=limit,
        ),
    }
