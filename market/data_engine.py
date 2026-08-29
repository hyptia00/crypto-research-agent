# ============================================================
# CRYPTO RESEARCH AGENT
# MARKET DATA ENGINE
# ============================================================

import time
import requests
import pandas as pd


BINANCE_BASE_URL = "https://api.binance.com"


# ------------------------------------------------------------
# HTTP
# ------------------------------------------------------------

def _get(endpoint, params=None, timeout=10):
    url = BINANCE_BASE_URL + endpoint

    response = requests.get(
        url,
        params=params or {},
        timeout=timeout,
        headers={
            "User-Agent": "crypto-research-agent/1.0"
        },
    )

    response.raise_for_status()
    return response.json()


# ------------------------------------------------------------
# KLINE DATA
# ------------------------------------------------------------

def get_klines(
    symbol,
    interval="1h",
    limit=200,
):
    """
    Binance Spot OHLCV verisini DataFrame olarak döndürür.
    """

    raw = _get(
        "/api/v3/klines",
        {
            "symbol": symbol.upper(),
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

    df = pd.DataFrame(raw, columns=columns)

    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "quote_volume",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

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

    return df


# ------------------------------------------------------------
# MULTI-TIMEFRAME DATA
# ------------------------------------------------------------

def get_multi_timeframe_data(
    symbol,
    timeframes=None,
    limit=200,
):
    """
    Bir coin için birden fazla timeframe verisi getirir.
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

        try:
            result[timeframe] = get_klines(
                symbol,
                timeframe,
                limit,
            )

        except Exception as exc:
            result[timeframe] = None
            print(
                f"{symbol} {timeframe} veri hatası: {exc}"
            )

        # Binance API'ye gereksiz yük bindirmemek için
        time.sleep(0.10)

    return result


# ------------------------------------------------------------
# 24H TICKER
# ------------------------------------------------------------

def get_24h_ticker(symbol):
    """
    Coin'in 24 saatlik piyasa verisini getirir.
    """

    data = _get(
        "/api/v3/ticker/24hr",
        {
            "symbol": symbol.upper(),
        },
    )

    return {
        "symbol": data.get("symbol"),
        "price": float(data.get("lastPrice", 0)),
        "price_change_percent": float(
            data.get("priceChangePercent", 0)
        ),
        "volume": float(
            data.get("volume", 0)
        ),
        "quote_volume": float(
            data.get("quoteVolume", 0)
        ),
        "high": float(
            data.get("highPrice", 0)
        ),
        "low": float(
            data.get("lowPrice", 0)
        ),
        "trades": int(
            data.get("count", 0)
        ),
    }


# ------------------------------------------------------------
# ALL USDT SYMBOLS
# ------------------------------------------------------------

def get_usdt_symbols():
    """
    Binance'teki aktif USDT spot paritelerini döndürür.
    """

    exchange_info = _get(
        "/api/v3/exchangeInfo"
    )

    symbols = []

    for item in exchange_info.get(
        "symbols",
        [],
    ):

        if item.get("status") != "TRADING":
            continue

        if item.get("quoteAsset") != "USDT":
            continue

        symbols.append(
            item.get("symbol")
        )

    return symbols


# ------------------------------------------------------------
# MARKET DISCOVERY
# ------------------------------------------------------------

def discover_usdt_markets(
    min_volume_usdt=5_000_000,
    limit=None,
):
    """
    USDT piyasasını tarar.

    Amaç:
    Ana coinler dışında likiditesi yeterli
    yeni fırsat adaylarını bulmak.
    """

    symbols = get_usdt_symbols()

    candidates = []

    for symbol in symbols:

        try:

            ticker = get_24h_ticker(
                symbol
            )

            quote_volume = ticker[
                "quote_volume"
            ]

            if quote_volume < min_volume_usdt:
                continue

            candidates.append(ticker)

        except Exception:
            continue

    candidates.sort(
        key=lambda x: x["quote_volume"],
        reverse=True,
    )

    if limit is not None:
        candidates = candidates[:limit]

    return candidates


# ------------------------------------------------------------
# PRICE
# ------------------------------------------------------------

def get_price(symbol):
    """
    Anlık fiyat.
    """

    data = _get(
        "/api/v3/ticker/price",
        {
            "symbol": symbol.upper(),
        },
    )

    return float(
        data["price"]
    )


# ------------------------------------------------------------
# MARKET SNAPSHOT
# ------------------------------------------------------------

def get_market_snapshot(symbol):
    """
    Tek coin için temel piyasa özeti.
    """

    ticker = get_24h_ticker(
        symbol
    )

    return {
        "symbol": symbol.upper(),
        "price": ticker["price"],
        "change_24h": ticker[
            "price_change_percent"
        ],
        "volume_24h": ticker[
            "quote_volume"
        ],
        "high_24h": ticker["high"],
        "low_24h": ticker["low"],
        "trades_24h": ticker["trades"],
    }


# ------------------------------------------------------------
# SAFE FETCH
# ------------------------------------------------------------

def safe_get_klines(
    symbol,
    interval,
    limit=200,
):
    """
    Veri alınamazsa programın tamamının
    çökmesini engeller.
    """

    try:

        df = get_klines(
            symbol,
            interval,
            limit,
        )

        if df.empty:
            return None

        return df

    except Exception as exc:

        print(
            f"VERİ ALMA HATASI | "
            f"{symbol} | {interval} | {exc}"
        )

        return None
