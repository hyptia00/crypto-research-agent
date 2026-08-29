# ============================================================
# CRYPTO RESEARCH AGENT
# MARKET OPPORTUNITY SCANNER
# ============================================================

from config import (
    CORE_COINS,
    MIN_24H_VOLUME_USDT,
)

from market.data_engine import (
    discover_usdt_markets,
)


# ============================================================
# SETTINGS
# ============================================================

DEFAULT_LIMIT = 30

MIN_ABSOLUTE_CHANGE = 1.0

MAX_ABSOLUTE_CHANGE = 30.0


# ============================================================
# HELPERS
# ============================================================

def _safe_float(value):

    try:
        return float(value)

    except (
        TypeError,
        ValueError,
    ):
        return 0.0


# ============================================================
# MOMENTUM SCORE
# ============================================================

def _momentum_score(
    change
):

    change = abs(
        _safe_float(change)
    )

    if change >= 10:
        return 3

    if change >= 5:
        return 2

    if change >= 2:
        return 1

    return 0


# ============================================================
# VOLUME SCORE
# ============================================================

def _volume_score(
    volume
):

    volume = _safe_float(
        volume
    )

    if volume >= 50_000_000:
        return 3

    if volume >= 20_000_000:
        return 2

    if volume >= 10_000_000:
        return 1

    return 0


# ============================================================
# DISCOVERY CANDIDATE
# ============================================================

def _build_candidate(
    ticker
):

    symbol = ticker.get(
        "symbol"
    )

    change = _safe_float(
        ticker.get(
            "price_change_percent"
        )
    )

    volume = _safe_float(
        ticker.get(
            "quote_volume"
        )
    )

    price = _safe_float(
        ticker.get(
            "price"
        )
    )

    if not symbol:
        return None

    if symbol in CORE_COINS:
        return None

    if not symbol.endswith(
        "USDT"
    ):
        return None

    if volume < MIN_24H_VOLUME_USDT:
        return None

    absolute_change = abs(
        change
    )

    # Aşırı hareket etmiş coinleri
    # ilk aşamada dışarıda bırak.
    if (
        absolute_change
        < MIN_ABSOLUTE_CHANGE
    ):
        return None

    if (
        absolute_change
        > MAX_ABSOLUTE_CHANGE
    ):
        return None

    momentum_score = (
        _momentum_score(
            change
        )
    )

    volume_score = (
        _volume_score(
            volume
        )
    )

    score = (
        momentum_score
        +
        volume_score
    )

    if score < 2:
        return None

    return {

        "symbol":
            symbol,

        "price":
            price,

        "change_24h":
            change,

        "volume_24h":
            volume,

        "discovery_score":
            score,

        "momentum_score":
            momentum_score,

        "volume_score":
            volume_score,

    }


# ============================================================
# DISCOVER
# ============================================================

def discover_candidates(
    limit=DEFAULT_LIMIT
):

    """
    Piyasadaki ana coinler dışındaki
    likit ve hareketli coinleri bulur.
    """

    print()
    print(
        "SCANNER: market discovery başlıyor..."
    )

    try:

        markets = discover_usdt_markets(

            min_volume_usdt=
                MIN_24H_VOLUME_USDT,

            limit=
                limit * 3,

        )

    except Exception as exc:

        print(
            "SCANNER ERROR:",
            exc
        )

        return []

    candidates = []

    for ticker in markets:

        candidate = (
            _build_candidate(
                ticker
            )
        )

        if candidate is None:
            continue

        candidates.append(
            candidate
        )

    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    candidates.sort(

        key=lambda x: (
            x["discovery_score"],
            x["volume_24h"],
            abs(x["change_24h"]),
        ),

        reverse=True,

    )

    candidates = candidates[
        :limit
    ]

    print(
        f"SCANNER: "
        f"{len(candidates)} aday bulundu."
    )

    return candidates


# ============================================================
# PRE-FILTER
# ============================================================

def prefilter_candidates(
    candidates
):

    """
    Strategy engine'e gönderilmeden önce
    gereksiz adayları temizler.
    """

    result = []

    for candidate in candidates:

        symbol = candidate.get(
            "symbol"
        )

        if not symbol:
            continue

        if symbol in CORE_COINS:
            continue

        if candidate.get(
            "volume_24h",
            0
        ) < MIN_24H_VOLUME_USDT:

            continue

        if candidate.get(
            "discovery_score",
            0
        ) < 2:

            continue

        result.append(
            candidate
        )

    return result


# ============================================================
# FINAL DISCOVERY
# ============================================================

def scan_market(
    limit=DEFAULT_LIMIT
):

    """
    Dışarıdan çağrılacak ana fonksiyon.

    Sonuç:
        Yeni coin adayları
    """

    candidates = (
        discover_candidates(
            limit=limit
        )
    )

    candidates = (
        prefilter_candidates(
            candidates
        )
    )

    return candidates


# ============================================================
# REPORT
# ============================================================

def print_scanner_report(
    candidates
):

    print()
    print("=" * 70)
    print(
        "NEW COIN DISCOVERY"
    )
    print("=" * 70)

    if not candidates:

        print(
            "Yeni aday bulunamadı."
        )

        return

    for index, candidate in enumerate(
        candidates,
        1
    ):

        print(
            f"{index:02d}. "
            f"{candidate['symbol']} | "
            f"24H: "
            f"{candidate['change_24h']:+.2f}% | "
            f"VOL: "
            f"${candidate['volume_24h']:,.0f} | "
            f"SCORE: "
            f"{candidate['discovery_score']}"
        )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    candidates = scan_market()

    print_scanner_report(
        candidates
    )
