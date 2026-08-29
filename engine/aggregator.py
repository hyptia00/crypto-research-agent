# ============================================================
# SIGNAL AGGREGATOR
# ============================================================

from typing import Any, Dict, List


def _score(signal: Dict[str, Any]) -> float:
    """
    Sinyalin karşılaştırılabilir skorunu üretir.
    Farklı stratejilerden gelen score formatlarını normalize eder.
    """

    value = signal.get("score", 0)

    try:
        value = float(value)
    except (TypeError, ValueError):
        value = 0.0

    # 4/5, 6/7 gibi string skorları destekle
    if isinstance(signal.get("score"), str):
        raw = signal["score"].strip()

        if "/" in raw:
            try:
                a, b = raw.split("/", 1)
                value = float(a) / float(b) * 10.0
            except (ValueError, ZeroDivisionError):
                value = 0.0

    return value


def _confidence(signal: Dict[str, Any]) -> float:
    """
    Confidence değerini 0-100 aralığına çevirir.
    """

    value = signal.get(
        "confidence",
        signal.get("guven", 0)
    )

    try:
        value = float(value)
    except (TypeError, ValueError):
        value = 0.0

    if value <= 1:
        value *= 100

    return max(0.0, min(100.0, value))


def _direction(signal: Dict[str, Any]) -> str:
    return str(
        signal.get(
            "direction",
            signal.get(
                "side",
                signal.get("signal", "")
            )
        )
    ).upper()


def _symbol(signal: Dict[str, Any]) -> str:
    return str(
        signal.get(
            "symbol",
            signal.get("coin", "")
        )
    ).upper()


def _strategy(signal: Dict[str, Any]) -> str:
    return str(
        signal.get(
            "strategy",
            signal.get("source", "UNKNOWN")
        )
    ).upper()


def aggregate_signals(
    signals: List[Dict[str, Any]],
    min_score: float = 6.0,
    min_confidence: float = 60.0,
) -> List[Dict[str, Any]]:
    """
    Futures / Spot / Scalping sinyallerini birleştirir.

    Aynı coin için karşıt yönlü sinyaller varsa
    doğrudan işlem sinyali üretmez.
    """

    if not signals:
        return []

    valid = []

    # --------------------------------------------------------
    # 1. NORMALIZE
    # --------------------------------------------------------

    for signal in signals:

        if not isinstance(signal, dict):
            continue

        symbol = _symbol(signal)
        direction = _direction(signal)

        if not symbol:
            continue

        if direction not in ("LONG", "SHORT", "BUY", "SELL"):
            continue

        if direction == "BUY":
            direction = "LONG"

        elif direction == "SELL":
            direction = "SHORT"

        item = dict(signal)

        item["symbol"] = symbol
        item["direction"] = direction
        item["strategy"] = _strategy(signal)
        item["_score"] = _score(signal)
        item["_confidence"] = _confidence(signal)

        valid.append(item)

    # --------------------------------------------------------
    # 2. GROUP BY SYMBOL
    # --------------------------------------------------------

    grouped = {}

    for signal in valid:

        symbol = signal["symbol"]

        grouped.setdefault(
            symbol,
            []
        ).append(signal)

    final = []

    # --------------------------------------------------------
    # 3. ANALYZE EACH COIN
    # --------------------------------------------------------

    for symbol, candidates in grouped.items():

        longs = [
            x for x in candidates
            if x["direction"] == "LONG"
        ]

        shorts = [
            x for x in candidates
            if x["direction"] == "SHORT"
        ]

        long_score = sum(
            x["_score"]
            for x in longs
        )

        short_score = sum(
            x["_score"]
            for x in shorts
        )

        # ----------------------------------------------------
        # CONFLICT FILTER
        # ----------------------------------------------------

        if longs and shorts:

            difference = abs(
                long_score - short_score
            )

            # Yönler birbirine çok yakınsa işlem yok
            if difference < 2.0:

                final.append({
                    "symbol": symbol,
                    "direction": "WAIT",
                    "action": "NO_TRADE",
                    "confidence": 0,
                    "reason":
                        "STRATEGY_CONFLICT",
                    "strategies": [
                        _strategy(x)
                        for x in candidates
                    ],
                })

                continue

        # ----------------------------------------------------
        # SELECT DIRECTION
        # ----------------------------------------------------

        if long_score > short_score:

            direction = "LONG"
            selected = longs
            opposing = shorts

        elif short_score > long_score:

            direction = "SHORT"
            selected = shorts
            opposing = longs

        else:

            final.append({
                "symbol": symbol,
                "direction": "WAIT",
                "action": "NO_TRADE",
                "confidence": 0,
                "reason": "NO_DIRECTIONAL_EDGE",
            })

            continue

        # ----------------------------------------------------
        # BEST CANDIDATE
        # ----------------------------------------------------

        selected = sorted(
            selected,
            key=lambda x: (
                x["_score"],
                x["_confidence"]
            ),
            reverse=True,
        )

        best = selected[0]

        score = best["_score"]
        confidence = best["_confidence"]

        # ----------------------------------------------------
        # AGREEMENT BONUS
        # ----------------------------------------------------

        agreement = len(selected)

        if agreement >= 2:
            confidence += 5

        if agreement >= 3:
            confidence += 5

        # Opposing strategy varsa güven azalt
        if opposing:
            confidence -= 10

        confidence = max(
            0,
            min(100, confidence)
        )

        # ----------------------------------------------------
        # MINIMUM QUALITY FILTER
        # ----------------------------------------------------

        if (
            score < min_score
            or confidence < min_confidence
        ):

            final.append({
                "symbol": symbol,
                "direction": "WAIT",
                "action": "NO_TRADE",
                "confidence": round(
                    confidence,
                    1
                ),
                "score": round(
                    score,
                    2
                ),
                "reason":
                    "QUALITY_FILTER",
                "best_strategy":
                    best["strategy"],
            })

            continue

        # ----------------------------------------------------
        # FINAL CANDIDATE
        # ----------------------------------------------------

        result = dict(best)

        result.pop(
            "_score",
            None
        )

        result.pop(
            "_confidence",
            None
        )

        result["symbol"] = symbol
        result["direction"] = direction
        result["action"] = (
            "LONG"
            if direction == "LONG"
            else "SHORT"
        )

        result["confidence"] = round(
            confidence,
            1
        )

        result["agreement"] = agreement

        result["strategies"] = [
            _strategy(x)
            for x in selected
        ]

        result["aggregated"] = True

        final.append(result)

    # --------------------------------------------------------
    # 4. SORT BEST FIRST
    # --------------------------------------------------------

    final.sort(
        key=lambda x: (
            float(
                x.get(
                    "confidence",
                    0
                )
            ),
            float(
                x.get(
                    "score",
                    0
                )
            ),
        ),
        reverse=True,
    )

    return final


def get_best_signal(
    signals: List[Dict[str, Any]],
    min_score: float = 6.0,
    min_confidence: float = 60.0,
):
    """
    Tek bir en iyi sinyali döndürür.
    """

    results = aggregate_signals(
        signals,
        min_score=min_score,
        min_confidence=min_confidence,
    )

    tradable = [
        x for x in results
        if x.get("action")
        in ("LONG", "SHORT")
    ]

    if not tradable:
        return None

    return tradable[0]
