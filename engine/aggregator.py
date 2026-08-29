# ============================================================
# SIGNAL AGGREGATOR
# ============================================================

from collections import defaultdict


# ============================================================
# HELPERS
# ============================================================

def _num(value, default=0.0):

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ============================================================
# SIGNAL QUALITY
# ============================================================

def _quality(signal):

    score = _num(
        signal.get("score"),
        0
    )

    confidence = _num(
        signal.get("confidence"),
        0
    )

    rr = _num(
        signal.get("rr"),
        0
    )

    # Yapısal teyit bonusları
    bonus = 0

    if signal.get("msb"):
        bonus += 2

    if signal.get("choch"):
        bonus += 1

    if signal.get("liquidity_sweep"):
        bonus += 2

    if signal.get("fvg"):
        bonus += 1

    # Nihai kalite
    quality = (
        score * 0.50
        +
        confidence * 0.30
        +
        min(rr, 4.0) * 2.5
        +
        bonus
    )

    return quality


# ============================================================
# AGGREGATE
# ============================================================

def aggregate_signals(
    signals,
    min_score=6,
    min_confidence=60,
):

    if not signals:
        return []

    grouped = defaultdict(list)

    # --------------------------------------------------------
    # GROUP BY SYMBOL + DIRECTION
    # --------------------------------------------------------

    for signal in signals:

        if not isinstance(
            signal,
            dict
        ):
            continue

        symbol = signal.get(
            "symbol"
        )

        direction = str(
            signal.get(
                "direction",
                "WAIT"
            )
        ).upper()

        if not symbol:
            continue

        if direction not in (
            "LONG",
            "SHORT",
        ):
            continue

        grouped[
            (
                symbol,
                direction
            )
        ].append(
            signal
        )

    results = []

    # ========================================================
    # PROCESS GROUPS
    # ========================================================

    for (
        symbol,
        direction
    ), group in grouped.items():

        # ----------------------------------------------------
        # FILTER
        # ----------------------------------------------------

        valid = []

        for signal in group:

            score = _num(
                signal.get(
                    "score"
                )
            )

            confidence = _num(
                signal.get(
                    "confidence"
                )
            )

            if (
                score >= min_score
                and
                confidence >= min_confidence
            ):

                valid.append(
                    signal
                )

        if not valid:
            continue

        # ----------------------------------------------------
        # STRATEGIES
        # ----------------------------------------------------

        strategy_names = []

        for signal in valid:

            strategy = signal.get(
                "strategy"
            )

            if strategy:
                strategy_names.append(
                    strategy
                )

        strategy_names = list(
            dict.fromkeys(
                strategy_names
            )
        )

        # ----------------------------------------------------
        # BEST SIGNAL
        # ----------------------------------------------------

        best = max(
            valid,
            key=_quality
        )

        # ----------------------------------------------------
        # WEIGHTED SCORE
        # ----------------------------------------------------

        total_weight = 0.0
        weighted_score = 0.0
        weighted_confidence = 0.0

        for signal in valid:

            strategy = str(
                signal.get(
                    "strategy",
                    ""
                )
            ).upper()

            # Scalping daha hızlı,
            # Futures ana yön açısından daha güçlü.
            if strategy == "FUTURES":
                weight = 1.25

            elif strategy == "SPOT":
                weight = 1.00

            elif strategy == "SCALPING":
                weight = 0.90

            else:
                weight = 0.75

            quality = _quality(
                signal
            )

            weighted_score += (
                _num(
                    signal.get(
                        "score"
                    )
                )
                *
                weight
            )

            weighted_confidence += (
                _num(
                    signal.get(
                        "confidence"
                    )
                )
                *
                weight
            )

            total_weight += weight

        if total_weight <= 0:
            continue

        avg_score = (
            weighted_score
            /
            total_weight
        )

        avg_confidence = (
            weighted_confidence
            /
            total_weight
        )

        # ----------------------------------------------------
        # AGREEMENT BONUS
        # ----------------------------------------------------

        agreement_bonus = 0

        unique_strategies = len(
            set(strategy_names)
        )

        if unique_strategies >= 2:

            agreement_bonus += 2

        if unique_strategies >= 3:

            agreement_bonus += 2

        # ----------------------------------------------------
        # STRUCTURE BONUS
        # ----------------------------------------------------

        structure_bonus = 0

        if any(
            s.get("msb")
            for s in valid
        ):

            structure_bonus += 2

        if any(
            s.get("liquidity_sweep")
            for s in valid
        ):

            structure_bonus += 2

        if any(
            s.get("choch")
            for s in valid
        ):

            structure_bonus += 1

        # ----------------------------------------------------
        # FINAL SCORE
        # ----------------------------------------------------

        final_score = (
            avg_score
            +
            agreement_bonus
            +
            structure_bonus
        )

        final_confidence = min(
            99,
            avg_confidence
            +
            agreement_bonus * 2
            +
            structure_bonus * 2
        )

        # ----------------------------------------------------
        # COPY BEST SIGNAL
        # ----------------------------------------------------

        result = dict(
            best
        )

        result.update({

            "symbol":
                symbol,

            "direction":
                direction,

            "strategy":
                "AGGREGATED",

            "strategies":
                strategy_names,

            "strategy_count":
                unique_strategies,

            "score":
                round(
                    final_score,
                    2
                ),

            "confidence":
                round(
                    final_confidence,
                    1
                ),

            "agreement_bonus":
                agreement_bonus,

            "structure_bonus":
                structure_bonus,

            "source_signals":
                valid,

            "source_count":
                len(valid),

        })

        results.append(
            result
        )

    # ========================================================
    # REMOVE CONFLICTS
    # ========================================================

    final = []

    by_symbol = defaultdict(
        list
    )

    for signal in results:

        by_symbol[
            signal["symbol"]
        ].append(
            signal
        )

    for symbol, candidates in (
        by_symbol.items()
    ):

        if len(candidates) == 1:

            final.append(
                candidates[0]
            )
            continue

        # LONG ve SHORT aynı anda
        # güçlü şekilde mevcutsa işlem yok.
        long_signal = next(
            (
                x for x in candidates
                if x["direction"] == "LONG"
            ),
            None
        )

        short_signal = next(
            (
                x for x in candidates
                if x["direction"] == "SHORT"
            ),
            None
        )

        if (
            long_signal
            and short_signal
        ):

            long_quality = _quality(
                long_signal
            )

            short_quality = _quality(
                short_signal
            )

            # Bir taraf belirgin şekilde
            # üstün değilse çatışma.
            difference = abs(
                long_quality
                -
                short_quality
            )

            if difference < 5:

                continue

            if long_quality > short_quality:

                final.append(
                    long_signal
                )

            else:

                final.append(
                    short_signal
                )

    # ========================================================
    # SORT
    # ========================================================

    final.sort(
        key=lambda x: (
            _num(
                x.get(
                    "confidence"
                )
            ),
            _num(
                x.get(
                    "score"
                )
            ),
            _num(
                x.get(
                    "rr"
                )
            ),
        ),
        reverse=True,
    )

    return final
