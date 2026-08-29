# ============================================================
# MARKET DATA ENGINE
# ============================================================

import time
import requests
import pandas as pd


BASE_URL = "https://api.binance.com"

KLINE_ENDPOINT = (
    "/api/v3/klines"
)

TICKER_ENDPOINT = (
    "/api/v3/ticker/24hr"
)


# ============================================================
# HTTP
# ============================================================

def _get(
    endpoint,
    params=None,
    timeout=15,
):

    response = requests.get(
        BASE_URL + endpoint,
        params=params,
        timeout=timeout,
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# KLINES
# ============================================================

def get_klines(
    symbol,
    interval,
    limit=200,
):

    symbol = symbol.upper()

    raw = _get(
        KLINE_ENDPOINT,
        {
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
        },
    )

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
    # INDEX
    # --------------------------------------------------------

    df = df.set_index(
        "open_time"
    )

    return df


# ============================================================
# MULTI TIMEFRAME
# ============================================================

def get_multi_timeframe_data(
    symbol,
    timeframes=None,
    limit=200,
):

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

            data[timeframe] = get_klines(
                symbol,
                timeframe,
                limit,
            )

        except Exception as exc:

            print(
                f"DATA ERROR "
                f"{symbol} "
                f"{timeframe}: "
                f"{exc}"
            )

            data[timeframe] = pd.DataFrame()

        # Binance API'yi gereksiz zorlamamak için
        # küçük bekleme.
        time.sleep(0.10)

    return data


# ============================================================
# PRICE
# ============================================================

def get_price(
    symbol,
):

    symbol = symbol.upper()

    data = _get(
        TICKER_ENDPOINT,
        {
            "symbol": symbol,
        },
    )

    return float(
        data["lastPrice"]
    )


# ============================================================
# ALL USDT MARKETS
# ============================================================

def get_usdt_tickers():

    raw = _get(
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
                ""
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

    tickers = get_usdt_tickers()

    candidates = []

    for ticker in tickers:

        symbol = str(
            ticker.get(
                "symbol",
                ""
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
                    0
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
                    0
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
                    0
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
    # RANK BY VOLUME
    # --------------------------------------------------------

    candidates.sort(

        key=lambda x:
            x["quote_volume"],

        reverse=True,

    )

    return candidates[:limit]


# ============================================================
# COMPATIBILITY
# ============================================================

def get_market_data(
    symbol,
    timeframe="15m",
    limit=200,
):

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

    return get_klines(
        symbol,
        timeframe,
        limit,
    )
