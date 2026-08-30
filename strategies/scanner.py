# ============================================================
# MARKET OPPORTUNITY SCANNER
# ============================================================

from typing import Any, Dict, List, Optional


# ============================================================
# DEFAULT SETTINGS
# ============================================================

DEFAULT_MIN_VOLUME = 10_000_000
DEFAULT_MAX_RESULTS = 15


# ============================================================
# HELPERS
# ============================================================

def _float(
    value,
    default=0.0,
):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _symbol(
    ticker,
):
    if not isinstance(ticker, dict):
        return ""

    return str(
        ticker.get(
            "symbol",
            "",
        )
    ).upper()


def _volume(
    ticker,
):
    if not isinstance(ticker, dict):
        return 0.0

    return _float(
        ticker.get(
            "quoteVolume",
            ticker.get(
                "quote_volume",
                ticker.get(
                    "volume",
                    0,
                ),
            ),
        ),
    )


def _change(
    ticker,
):
    if not isinstance(ticker, dict):
        return 0.0

    return _float(
        ticker.get(
            "priceChangePercent",
            ticker.get(
                "price_change_percent",
                0,
            ),
        ),
    )


def _price(
    ticker,
):
    if not isinstance(ticker, dict):
        return 0.0

    return _float(
        ticker.get(
            "lastPrice",
            ticker.get(
                "last_price",
                ticker.get(
                    "price",
                    0,
                ),
            ),
        ),
    )


# ============================================================
# MOMENTUM SCORE
# ============================================================

def _momentum_score(
    change,
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


# ============================================================
# VOLUME SCORE
# ============================================================

def _volume_score(
    volume,
):
    volume = _float(
        volume
    )

    if volume >= 100_000_000:
        return 4

    if volume >= 50_000_000:
        return 3

    if volume >= 20_000_000:
        return 2

    if volume >= 10_000_000:
        return 1

    return 0


# ============================================================
# BUILD CANDIDATE
# ============================================================

def _build_candidate(
    ticker,
    core_coins,
    min_volume,
):
    symbol = _symbol(
        ticker
    )

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

    # --------------------------------------------------------
    # MARKET DATA
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # LOW ACTIVITY FILTER
    # --------------------------------------------------------

    if abs(change) < 1.5:
        return None

    # --------------------------------------------------------
    # SCORES
    # --------------------------------------------------------

    momentum = _momentum_score(
        change
    )

    volume_score = _volume_score(
        volume
    )

    discovery_score = (
        momentum
        +
        volume_score
    )

    if discovery_score < 2:
        return None

    # --------------------------------------------------------
    # EXTREME MOVE
    # --------------------------------------------------------

    extreme = (
        abs(change) >= 15
    )

    # --------------------------------------------------------
    # DIRECTION BIAS
    # --------------------------------------------------------

    if change > 0:
        bias = "LONG_BIAS"

    elif change < 0:
        bias = "SHORT_BIAS"

    else:
        bias = "NEUTRAL"

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    return {
        "symbol": symbol,

        "price": price,

        "change_24h": change,

        "volume_24h": volume,

        "momentum_score": momentum,

        "volume_score": volume_score,

        "discovery_score": discovery_score,

        "extreme_move": extreme,

        "bias": bias,

        "source": "MARKET_SCANNER",
    }


# ============================================================
# MARKET SCANNER
# ============================================================

def scan_market(
    tickers: Optional[
        List[Dict[str, Any]]
    ] = None,

    core_coins: Optional[
        List[str]
    ] = None,

    min_volume: float = DEFAULT_MIN_VOLUME,

    limit: int = DEFAULT_MAX_RESULTS,
):
    """
    Piyasadaki yeni fırsat adaylarını bulur.

    Bu fonksiyon:

        - işlem açmaz
        - BUY/SELL emri üretmez
        - pozisyon açmaz
        - sadece aday coinleri bulur

    Nihai işlem kararı:
        Futures / Spot / Scalping
        stratejilerine bırakılır.
    """

    if not tickers:
        return []

    # --------------------------------------------------------
    # NORMALIZE CORE COINS
    # --------------------------------------------------------

    core = {
        str(x).upper()
        for x in (
            core_coins or []
        )
    }

    # --------------------------------------------------------
    # VALIDATE LIMIT
    # --------------------------------------------------------

    try:
        limit = int(
            limit
        )
    except (
        TypeError,
        ValueError,
    ):
        limit = DEFAULT_MAX_RESULTS

    if limit <= 0:
        return []

    # --------------------------------------------------------
    # VALIDATE VOLUME
    # --------------------------------------------------------

    min_volume = _float(
        min_volume,
        DEFAULT_MIN_VOLUME,
    )

    if min_volume < 0:
        min_volume = 0

    # --------------------------------------------------------
    # SCAN
    # --------------------------------------------------------

    candidates = []

    for ticker in tickers:

        candidate = _build_candidate(
            ticker=ticker,
            core_coins=core,
            min_volume=min_volume,
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
            _float(
                x.get(
                    "discovery_score",
                )
            ),

            _float(
                x.get(
                    "volume_24h",
                )
            ),

            abs(
                _float(
                    x.get(
                        "change_24h",
                    )
                )
            ),
        ),
        reverse=True,
    )

    return candidates[
        :limit
    ]


# ============================================================
# RANK CANDIDATES
# ============================================================

def rank_candidates(
    candidates,
):
    """
    Mevcut adayları tekrar sıralar.
    """

    if not candidates:
        return []

    valid = [
        candidate
        for candidate in candidates
        if isinstance(
            candidate,
            dict,
        )
    ]

    return sorted(
        valid,
        key=lambda x: (
            _float(
                x.get(
                    "discovery_score",
                )
            ),

            _float(
                x.get(
                    "volume_24h",
                )
            ),

            abs(
                _float(
                    x.get(
                        "change_24h",
                    )
                )
            ),
        ),
        reverse=True,
    )


# ============================================================
# REMOVE CORE COINS
# ============================================================

def remove_core_coins(
    candidates,
    core_coins,
):
    """
    Core coinleri aday listesinden çıkarır.
    """

    if not candidates:
        return []

    core = {
        str(x).upper()
        for x in (
            core_coins or []
        )
    }

    result = []

    for candidate in candidates:

        if not isinstance(
            candidate,
            dict,
        ):
            continue

        symbol = str(
            candidate.get(
                "symbol",
                "",
            )
        ).upper()

        if symbol in core:
            continue

        result.append(
            candidate
        )

    return result


# ============================================================
# PRINT SCANNER REPORT
# ============================================================

def print_scanner_report(
    candidates,
):
    """
    Scanner sonuçlarını terminale okunabilir
    şekilde yazdırır.

    Bu fonksiyon sadece raporlama yapar.
    """

    print()
    print(
        "=" * 80
    )

    print(
        "MARKET OPPORTUNITY SCANNER"
    )

    print(
        "=" * 80
    )

    if not candidates:

        print(
            "No new market candidates found."
        )

        print(
            "=" * 80
        )

        return

    print(
        f"Candidates: {len(candidates)}"
    )

    print()

    for index, candidate in enumerate(
        candidates,
        start=1,
    ):

        symbol = candidate.get(
            "symbol",
            "?",
        )

        price = _float(
            candidate.get(
                "price",
            )
        )

        change = _float(
            candidate.get(
                "change_24h",
            )
        )

        volume = _float(
            candidate.get(
                "volume_24h",
            )
        )

        score = _float(
            candidate.get(
                "discovery_score",
            )
        )

        bias = candidate.get(
            "bias",
            "NEUTRAL",
        )

        extreme = candidate.get(
            "extreme_move",
            False,
        )

        print(
            f"{index:02d}. "
            f"{symbol:<15} "
            f"24h: {change:>7.2f}% "
            f"Vol: ${volume:>12,.0f} "
            f"Score: {score:>4.1f} "
            f"{bias}"
        )

        if extreme:

            print(
                "    WARNING: EXTREME 24H MOVE"
            )

    print()

    print(
        "=" * 80
    )
