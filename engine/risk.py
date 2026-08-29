# ============================================================
# RISK ENGINE
# FINAL TRADE FILTER
# ============================================================

def _num(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _side(value):
    value = str(value or "").upper()

    if value in ("LONG", "BUY"):
        return "LONG"

    if value in ("SHORT", "SELL"):
        return "SHORT"

    return "WAIT"


# ============================================================
# SINGLE SIGNAL CHECK
# ============================================================

def validate_signal(
    signal,
    btc_regime="UNKNOWN",
    min_confidence=60,
    min_rr=1.8,
):
    if not isinstance(signal, dict):
        return False, "INVALID_SIGNAL"

    direction = _side(
        signal.get("direction")
    )

    if direction == "WAIT":
        return False, "NO_DIRECTION"

    score = _num(
        signal.get("score")
    )

    confidence = _num(
        signal.get("confidence")
    )

    rr = _num(
        signal.get("rr")
    )

    if confidence < min_confidence:
        return False, "CONFIDENCE_TOO_LOW"

    if rr < min_rr:
        return False, "RISK_REWARD_TOO_LOW"

    if score <= 0:
        return False, "INVALID_SCORE"

    entry = _num(
        signal.get("entry")
    )

    stop = _num(
        signal.get("stop")
    )

    tp1 = _num(
        signal.get("tp1")
    )

    tp2 = _num(
        signal.get("tp2")
    )

    if entry <= 0:
        return False, "INVALID_ENTRY"

    if stop <= 0:
        return False, "INVALID_STOP"

    if tp1 <= 0 or tp2 <= 0:
        return False, "INVALID_TARGET"

    # --------------------------------------------------------
    # LONG LEVEL VALIDATION
    # --------------------------------------------------------

    if direction == "LONG":

        if stop >= entry:
            return False, "LONG_STOP_INVALID"

        if tp1 <= entry:
            return False, "LONG_TP1_INVALID"

        if tp2 <= tp1:
            return False, "LONG_TP2_INVALID"

    # --------------------------------------------------------
    # SHORT LEVEL VALIDATION
    # --------------------------------------------------------

    if direction == "SHORT":

        if stop <= entry:
            return False, "SHORT_STOP_INVALID"

        if tp1 >= entry:
            return False, "SHORT_TP1_INVALID"

        if tp2 >= tp1:
            return False, "SHORT_TP2_INVALID"

    # --------------------------------------------------------
    # BTC REGIME
    # --------------------------------------------------------

    regime = _side(
        btc_regime
    )

    # BTC ters yöndeyse tamamen yasaklamıyoruz.
    # Ancak risk puanını düşürmek için metadata bırakıyoruz.
    if (
        regime in ("LONG", "SHORT")
        and regime != direction
    ):
        signal["btc_conflict"] = True
    else:
        signal["btc_conflict"] = False

    return True, "VALID"


# ============================================================
# FINAL SIGNAL
# ============================================================

def get_final_signal(
    signals,
    btc_regime="UNKNOWN",
    min_confidence=60,
    min_rr=1.8,
):
    if not signals:
        return None

    valid = []

    for signal in signals:

        ok, reason = validate_signal(
            signal,
            btc_regime=btc_regime,
            min_confidence=min_confidence,
            min_rr=min_rr,
        )

        if not ok:
            continue

        item = dict(signal)

        item["risk_status"] = "APPROVED"
        item["risk_reason"] = reason

        valid.append(item)

    if not valid:
        return None

    # --------------------------------------------------------
    # RANK
    # --------------------------------------------------------

    def ranking(signal):

        confidence = _num(
            signal.get("confidence")
        )

        score = _num(
            signal.get("score")
        )

        rr = _num(
            signal.get("rr")
        )

        conflict_penalty = (
            8
            if signal.get("btc_conflict")
            else 0
        )

        return (
            confidence * 0.50
            +
            score * 4
            +
            min(rr, 4) * 5
            -
            conflict_penalty
        )

    best = max(
        valid,
        key=ranking
    )

    # --------------------------------------------------------
    # FINAL CONFIDENCE
    # --------------------------------------------------------

    confidence = _num(
        best.get("confidence")
    )

    if best.get("btc_conflict"):
        confidence -= 8

    confidence = max(
        0,
        min(99, confidence)
    )

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    result = dict(best)

    result["confidence"] = round(
        confidence,
        1
    )

    result["risk_status"] = "APPROVED"

    result["execution_ready"] = True

    return result


# ============================================================
# POSITION SIZE
# ============================================================

def calculate_position_size(
    balance,
    entry,
    stop,
    risk_per_trade=0.01,
):
    balance = _num(balance)
    entry = _num(entry)
    stop = _num(stop)
    risk_per_trade = _num(
        risk_per_trade,
        0.01
    )

    if (
        balance <= 0
        or entry <= 0
        or stop <= 0
    ):
        return 0.0

    risk_amount = (
        balance
        *
        risk_per_trade
    )

    stop_distance = abs(
        entry - stop
    )

    if stop_distance <= 0:
        return 0.0

    quantity = (
        risk_amount
        /
        stop_distance
    )

    return quantity


# ============================================================
# MAX LOSS CHECK
# ============================================================

def daily_loss_allowed(
    starting_balance,
    current_balance,
    max_daily_loss=0.03,
):
    starting_balance = _num(
        starting_balance
    )

    current_balance = _num(
        current_balance
    )

    max_daily_loss = _num(
        max_daily_loss,
        0.03
    )

    if starting_balance <= 0:
        return False

    loss = (
        starting_balance
        -
        current_balance
    )

    loss_ratio = (
        loss
        /
        starting_balance
    )

    return loss_ratio < max_daily_loss
