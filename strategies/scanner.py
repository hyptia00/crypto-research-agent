# ============================================================
# MARKET OPPORTUNITY SCANNER
# ============================================================

from typing import Any, Dict, List, Optional


DEFAULT_MIN_VOLUME = 10_000_000
DEFAULT_MAX_RESULTS = 15


def _float(value, default=0.0):

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _symbol(ticker):

    return str(
        ticker.get(
            "symbol",
            ""
        )
    ).upper()


def _volume(ticker):

    return _float(
        ticker.get(
            "quoteVolume",
            ticker.get(
                "quote_volume",
                ticker.get(
                    "volume",
                    0
                )
            )
        )
    )


def _change(ticker):

    return _float(
        ticker.get(
            "priceChangePercent",
            ticker.get(
                "price_change_percent",
                0
            )
        )
    )


def _price(ticker):

    return _float(
        ticker.get(
            "lastPrice",
            ticker.get(
                "price",
                0
            )
        )
    )


def _momentum_score(
    change
):

    change = abs(
        _float(change)
    )

    if change >= 10:
        return 4

    if change >= 7:
        return 3

    if change >= 4:
        return 2

    if change >= 2:
        return 1

    return 0


def _volume_score(
    volume
):

    if volume >= 100_000_000:
        return 4

    if volume >= 50_000_000:
        return 3

    if volume >= 20_000_000:
        return 2

    if volume >= 10_000_000:
        return 1

    return 0


def _build_candidate(
    ticker,
    core_coins,
    min_volume
):

    symbol = _symbol(ticker)

    if not symbol:
        return None

    # --------------------------------------------------------
    # USDT ONLY
    # --------------------------------------------------------

    if not symbol.endswith(
        "USDT"
    ):
        return None

    # --------------------------------------------------------
    # CORE COINS EXCLUDED
    # --------------------------------------------------------

    if symbol in core_coins:
        return None

    volume = _volume(
        ticker
    )

    change = _change(
        ticker
    )

    price = _price(
        ticker
    )

    if volume < min_volume:
        return None

    if price <= 0:
        return None

    # Çok düşük hareket = ilgi yok
    if abs(change) < 1.5:
        return None

    momentum = _momentum_score(
        change
    )

    volume_score = _volume_score(
        volume
    )

    score = (
        momentum
        +
        volume_score
    )

    if score < 2:
        return None

    # --------------------------------------------------------
    # EXTREME MOVE FLAG
    # --------------------------------------------------------

    extreme = (
        abs(change) >= 15
    )

    return {

        "symbol":
            symbol,

        "price":
            price,

        "change_24h":
            change,

        "volume_24h":
            volume,

        "momentum_score":
            momentum,

        "volume_score":
            volume_score,

        "discovery_score":
            score,

        "extreme_move":
            extreme,

        "source":
            "MARKET_SCANNER",

    }


def scan_market(
    tickers: Optional[List[Dict[str, Any]]] = None,
    core_coins: Optional[List[str]] = None,
    min_volume: float = DEFAULT_MIN_VOLUME,
    limit: int = DEFAULT_MAX_RESULTS,
):

    """
    Piyasadaki yeni fırsatları bulur.

    Bu fonksiyon:
        - işlem açmaz
        - BUY/SELL üretmez
        - sadece aday bulur
    """

    if not tickers:
        return []

    core = {
        str(x).upper()
        for x in (
            core_coins or []
        )
    }

    candidates = []

    for ticker in tickers:

        candidate = _build_candidate(
            ticker,
            core,
            min_volume,
        )

        if candidate is None:
            continue

        candidates.append(
            candidate
        )

    # --------------------------------------------------------
    # RANK
    # --------------------------------------------------------

    candidates.sort(

        key=lambda x: (
            x["discovery_score"],
            x["volume_24h"],
            abs(x["change_24h"]),
        ),

        reverse=True,
    )

    return candidates[:limit]


def rank_candidates(
    candidates
):

    """
    Mevcut adayları tekrar sıralar.
    """

    if not candidates:
        return []

    return sorted(

        candidates,

        key=lambda x: (
            _float(
                x.get(
                    "discovery_score"
                )
            ),

            _float(
                x.get(
                    "volume_24h"
                )
            ),

            abs(
                _float(
                    x.get(
                        "change_24h"
                    )
                )
            ),
        ),

        reverse=True,
    )


def remove_core_coins(
    candidates,
    core_coins
):

    core = {
        str(x).upper()
        for x in (
            core_coins or []
        )
    }

    return [
        candidate
        for candidate in candidates
        if str(
            candidate.get(
                "symbol",
                ""
            )
        ).upper()
        not in core
    ]
