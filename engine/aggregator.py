# ============================================================
# CRYPTO RESEARCH AGENT
# SIGNAL AGGREGATOR
# ============================================================

from config import (
    FUTURES_MIN_SCORE,
    SPOT_MIN_SCORE,
    SCALPING_MIN_SCORE,
)


# ============================================================
# HELPERS
# ============================================================

def _score(signal):
    try:
        return float(
            signal.get("score", 0)
        )
    except (TypeError, ValueError):
        return 0.0


def _confidence(signal):
    try:
        return float(
            signal.get("confidence", 0)
        )
    except (TypeError, ValueError):
        return 0.0


def _side(signal):
    return signal.get("side")


def _is_valid(signal):
    return (
        signal is not None
        and _side(signal) not in (
            None,
            "WAIT",
        )
        and _score(signal) > 0
    )


# ============================================================
# STRATEGY WEIGHTS
# ============================================================

def _weight(signal):

    market = signal.get(
        "market",
        ""
    )

    if market == "FUTURES":
        return 1.00

    if market == "SPOT":
        return 0.95

    if market == "SCALPING":
        return 0.90

    return 0.80


# ============================================================
# QUALITY
# ============================================================

def _quality(signal):

    score = _score(signal)
    confidence = _confidence(signal)

    weight = _weight(
        signal
    )

    return (
        score * 10 * weight
        +
        confidence * 0.25
    )


# ============================================================
# DIRECTION GROUPING
# ============================================================

def _group_by_direction(
    signals
):

    groups = {
        "LONG": [],
        "SHORT": [],
    }

    for signal in signals:

        side = _side(
            signal
        )

        if side in groups:
            groups[side].append(
                signal
            )

    return groups


# ============================================================
# AGREEMENT
# ============================================================

def _agreement_score(
    signals
):

    if not signals:
        return 0

    long_count = sum(
        1
        for x in signals
        if x.get("side") == "LONG"
    )

    short_count = sum(
        1
        for x in signals
        if x.get("side") == "SHORT"
    )

    if long_count > short_count:
        return long_count

    if short_count > long_count:
        return short_count

    return 0


# ============================================================
# BEST SIGNAL
# ============================================================

def _best_signal(
    signals
):

    if not signals:
        return None

    return max(
        signals,
        key=_quality
    )


# ============================================================
# FINAL CONFIDENCE
# ============================================================

def _calculate_confidence(
    selected,
    all_signals
):

    if not selected:
        return 0

    base = _confidence(
        selected
    )

    side = selected.get(
        "side"
    )

    confirmations = [
        x
        for x in all_signals
        if x.get("side") == side
    ]

    count = len(
        confirmations
    )

    # --------------------------------------------------------
    # STRATEGY AGREEMENT
    # --------------------------------------------------------

    if count >= 3:
        base += 15

    elif count == 2:
        base += 8

    # --------------------------------------------------------
    # QUALITY
    # --------------------------------------------------------

    if _score(selected) >= 10:
        base += 5

    return min(
        99,
        base
    )


# ============================================================
# RISK CONSISTENCY
# ============================================================

def _risk_consistent(
    signal
):

    if not signal:
        return False

    entry = signal.get(
        "entry"
    )

    stop = signal.get(
        "stop"
    )

    tp1 = signal.get(
        "tp1"
    )

    if (
        entry is None
        or stop is None
        or tp1 is None
    ):
        return False

    side = signal.get(
        "side"
    )

    try:

        entry = float(entry)
        stop = float(stop)
        tp1 = float(tp1)

    except (
        TypeError,
        ValueError,
    ):

        return False

    if side == "LONG":

        if stop >= entry:
            return False

        if tp1 <= entry:
            return False

    elif side == "SHORT":

        if stop <= entry:
            return False

        if tp1 >= entry:
            return False

    else:

        return False

    return True


# ============================================================
# STRATEGY THRESHOLD
# ============================================================

def _minimum_score(
    market
):

    if market == "FUTURES":
        return FUTURES_MIN_SCORE

    if market == "SPOT":
        return SPOT_MIN_SCORE

    if market == "SCALPING":
        return SCALPING_MIN_SCORE

    return 999


# ============================================================
# FILTER
# ============================================================

def filter_signals(
    signals
):

    result = []

    for signal in signals:

        if not _is_valid(
            signal
        ):
            continue

        market = signal.get(
            "market"
        )

        score = _score(
            signal
        )

        minimum = _minimum_score(
            market
        )

        if score < minimum:
            continue

        if not _risk_consistent(
            signal
        ):
            continue

        result.append(
            signal
        )

    return result


# ============================================================
# AGGREGATE
# ============================================================

def aggregate(
    signals
):

    """
    Futures / Spot / Scalping sinyallerini
    tek karar haline getirir.

    Aynı coin için:

        LONG + LONG + LONG
            ->
        güçlü consensus

        LONG + SHORT
            ->
        conflict

    """

    valid = filter_signals(
        signals
    )

    if not valid:
        return None

    groups = _group_by_direction(
        valid
    )

    long_signals = groups[
        "LONG"
    ]

    short_signals = groups[
        "SHORT"
    ]

    # ========================================================
    # CONFLICT
    # ========================================================

    if (
        long_signals
        and short_signals
    ):

        long_quality = sum(
            _quality(x)
            for x in long_signals
        )

        short_quality = sum(
            _quality(x)
            for x in short_signals
        )

        difference = abs(
            long_quality
            -
            short_quality
        )

        total = (
            long_quality
            +
            short_quality
        )

        # İki yön birbirine çok yakınsa:
        # İŞLEM YOK.
        if (
            total > 0
            and difference / total < 0.25
        ):

            return {
                "symbol":
                    valid[0].get(
                        "symbol"
                    ),

                "market":
                    "AGGREGATED",

                "side":
                    "WAIT",

                "score":
                    0,

                "confidence":
                    0,

                "status":
                    "CONFLICT",

                "reasons": [
                    "LONG/SHORT conflict"
                ],
            }

        if long_quality > short_quality:

            selected_pool = (
                long_signals
            )

        else:

            selected_pool = (
                short_signals
            )

    else:

        if long_signals:

            selected_pool = (
                long_signals
            )

        elif short_signals:

            selected_pool = (
                short_signals
            )

        else:

            return None

    # ========================================================
    # BEST
    # ========================================================

    selected = _best_signal(
        selected_pool
    )

    if not selected:
        return None

    # ========================================================
    # CONSENSUS
    # ========================================================

    side = selected.get(
        "side"
    )

    confirmations = [
        x
        for x in valid
        if x.get("side") == side
    ]

    agreement = len(
        confirmations
    )

    # ========================================================
    # CONFIDENCE
    # ========================================================

    confidence = (
        _calculate_confidence(
            selected,
            valid
        )
    )

    # ========================================================
    # COPY RESULT
    # ========================================================

    result = dict(
        selected
    )

    result.update({

        "market":
            "AGGREGATED",

        "source_market":
            selected.get(
                "market"
            ),

        "confirmations":
            agreement,

        "confidence":
            confidence,

        "status":
            "QUALIFIED",

    })

    # ========================================================
    # REASONS
    # ========================================================

    reasons = list(
        selected.get(
            "reasons",
            []
        )
    )

    for signal in confirmations:

        market = signal.get(
            "market"
        )

        if market not in str(
            reasons
        ):

            reasons.append(
                f"{market} confirmation"
            )

    result["reasons"] = reasons

    return result


# ============================================================
# MULTI-SYMBOL AGGREGATION
# ============================================================

def aggregate_many(
    symbol_signals
):

    """
    Birden fazla coin için:

        {
            "BTCUSDT": [...],
            "ETHUSDT": [...],
            ...
        }

    """

    results = []

    for symbol, signals in (
        symbol_signals.items()
    ):

        result = aggregate(
            signals
        )

        if result is None:
            continue

        if result.get(
            "side"
        ) == "WAIT":

            continue

        result["symbol"] = symbol

        results.append(
            result
        )

    # En yüksek confidence
    # önce gelir.
    results.sort(
        key=lambda x: (
            x.get(
                "confidence",
                0
            ),
            x.get(
                "score",
                0
            ),
            x.get(
                "confirmations",
                0
            ),
        ),
        reverse=True,
    )

    return results
