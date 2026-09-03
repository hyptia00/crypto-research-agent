# ============================================================
# SIGNAL AGGREGATOR
# ============================================================

from collections import defaultdict


# ============================================================
# CONSTANTS
# ============================================================

MAX_SOURCE_CONFIDENCE = 85.0
MAX_FINAL_CONFIDENCE = 94.0

SINGLE_STRATEGY_CAP = 75.0
TWO_STRATEGY_CAP = 88.0
THREE_STRATEGY_CAP = 94.0


# ============================================================
# HELPERS
# ============================================================

def _num(value, default=0.0):

    try:
        return float(value)

    except (
        TypeError,
        ValueError,
    ):
        return default


def _confidence(signal):

    value = _num(
        signal.get(
            "confidence",
            0,
        )
    )

    if value < 0:
        return 0.0

    return min(
        value,
        MAX_SOURCE_CONFIDENCE,
    )


def _strategy(signal):

    return str(
        signal.get(
            "strategy",
            "",
        )
    ).upper()


# ============================================================
# SIGNAL QUALITY
# ============================================================

def _quality(signal):

    score = _num(
        signal.get(
            "score",
            0,
        )
    )

    confidence = _confidence(
        signal
    )

    rr = _num(
        signal.get(
            "rr",
            0,
        )
    )

    # --------------------------------------------------------
    # STRUCTURAL CONFIRMATIONS
    # --------------------------------------------------------

    bonus = 0.0

    if signal.get(
        "msb",
        False,
    ):
        bonus += 2.0

    if signal.get(
        "choch",
        False,
    ):
        bonus += 1.0

    if signal.get(
        "liquidity_sweep",
        False,
    ):
        bonus += 2.0

    if signal.get(
        "fvg",
        False,
    ):
        bonus += 1.0

    # --------------------------------------------------------
    # QUALITY
    # --------------------------------------------------------

    quality = (

        score * 0.50

        +

        confidence * 0.30

        +

        min(
            max(rr, 0.0),
            4.0,
        ) * 2.5

        +

        bonus
    )

    return quality


# ============================================================
# STRATEGY WEIGHT
# ============================================================

def _strategy_weight(
    strategy
):

    strategy = str(
        strategy
    ).upper()

    if strategy == "FUTURES":

        return 1.25

    if strategy == "SPOT":

        return 1.00

    if strategy == "SCALPING":

        return 0.90

    return 0.75


# ============================================================
# CONFIDENCE CAP
# ============================================================

def _confidence_cap(
    strategy_count
):

    if strategy_count >= 3:

        return THREE_STRATEGY_CAP

    if strategy_count == 2:

        return TWO_STRATEGY_CAP

    return SINGLE_STRATEGY_CAP


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

    grouped = defaultdict(
        list
    )

    # ========================================================
    # GROUP BY SYMBOL + DIRECTION
    # ========================================================

    for signal in signals:

        if not isinstance(
            signal,
            dict,
        ):
            continue

        symbol = signal.get(
            "symbol"
        )

        if not symbol:
            continue

        symbol = str(
            symbol
        ).upper()

        direction = str(
            signal.get(
                "direction",
                "WAIT",
            )
        ).upper()

        if direction not in (
            "LONG",
            "SHORT",
        ):
            continue

        grouped[
            (
                symbol,
                direction,
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
        direction,
    ), group in grouped.items():

        # ----------------------------------------------------
        # FILTER WEAK SIGNALS
        # ----------------------------------------------------

        valid = []

        for signal in group:

            score = _num(
                signal.get(
                    "score",
                    0,
                )
            )

            confidence = _confidence(
                signal
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

        # ====================================================
        # STRATEGIES
        # ====================================================

        strategy_names = []

        for signal in valid:

            strategy = _strategy(
                signal
            )

            if (
                strategy
                and
                strategy not in strategy_names
            ):

                strategy_names.append(
                    strategy
                )

        unique_strategies = len(
            strategy_names
        )

        # ====================================================
        # BEST SIGNAL
        # ====================================================

        best = max(
            valid,
            key=_quality,
        )

        # ====================================================
        # WEIGHTED VALUES
        # ====================================================

        total_weight = 0.0

        weighted_score = 0.0

        weighted_confidence = 0.0

        for signal in valid:

            strategy = _strategy(
                signal
            )

            weight = _strategy_weight(
                strategy
            )

            score = _num(
                signal.get(
                    "score",
                    0,
                )
            )

            confidence = _confidence(
                signal
            )

            weighted_score += (
                score
                *
                weight
            )

            weighted_confidence += (
                confidence
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

        # ====================================================
        # AGREEMENT
        # ====================================================

        agreement_bonus = 0.0

        if unique_strategies >= 2:

            agreement_bonus += 2.0

        if unique_strategies >= 3:

            agreement_bonus += 2.0

        # ====================================================
        # STRUCTURE
        # ====================================================

        structure_bonus = 0.0

        if any(
            bool(
                s.get(
                    "msb",
                    False,
                )
            )
            for s in valid
        ):

            structure_bonus += 2.0

        if any(
            bool(
                s.get(
                    "liquidity_sweep",
                    False,
                )
            )
            for s in valid
        ):

            structure_bonus += 2.0

        if any(
            bool(
                s.get(
                    "choch",
                    False,
                )
            )
            for s in valid
        ):

            structure_bonus += 1.0

        # ====================================================
        # FINAL SCORE
        # ====================================================

        final_score = (

            avg_score

            +

            agreement_bonus

            +

            structure_bonus
        )

        # ====================================================
        # FINAL CONFIDENCE
        # ====================================================

        raw_confidence = (

            avg_confidence

            +

            agreement_bonus * 2.0

            +

            structure_bonus * 1.5
        )

        # ----------------------------------------------------
        # STRATEGY COUNT CAP
        # ----------------------------------------------------

        confidence_cap = _confidence_cap(
            unique_strategies
        )

        final_confidence = min(
            raw_confidence,
            confidence_cap,
            MAX_FINAL_CONFIDENCE,
        )

        # ====================================================
        # COPY BEST SIGNAL
        # ====================================================

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
                    2,
                ),

            "confidence":
                round(
                    final_confidence,
                    1,
                ),

            "agreement_bonus":
                agreement_bonus,

            "structure_bonus":
                structure_bonus,

            "source_signals":
                valid,

            "source_count":
                len(
                    valid
                ),

        })

        results.append(
            result
        )

    # ========================================================
    # REMOVE DIRECTION CONFLICTS
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

    for (
        symbol,
        candidates,
    ) in by_symbol.items():

        if len(
            candidates
        ) == 1:

            final.append(
                candidates[0]
            )

            continue

        long_signal = next(
            (
                x
                for x in candidates
                if x.get(
                    "direction"
                ) == "LONG"
            ),
            None,
        )

        short_signal = next(
            (
                x
                for x in candidates
                if x.get(
                    "direction"
                ) == "SHORT"
            ),
            None,
        )

        # ----------------------------------------------------
        # BOTH DIRECTIONS
        # ----------------------------------------------------

        if (
            long_signal
            and
            short_signal
        ):

            long_quality = _quality(
                long_signal
            )

            short_quality = _quality(
                short_signal
            )

            difference = abs(
                long_quality
                -
                short_quality
            )

            # Belirgin üstünlük yoksa WAIT.
            if difference < 5.0:

                continue

            if (
                long_quality
                >
                short_quality
            ):

                final.append(
                    long_signal
                )

            else:

                final.append(
                    short_signal
                )

    # ========================================================
    # FINAL SORT
    # ========================================================

    final.sort(

        key=lambda x: (

            _num(
                x.get(
                    "confidence",
                    0,
                )
            ),

            _num(
                x.get(
                    "score",
                    0,
                )
            ),

            _num(
                x.get(
                    "rr",
                    0,
                )
            ),
        ),

        reverse=True,
    )

    return final
