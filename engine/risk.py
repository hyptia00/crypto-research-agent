# ============================================================
# RISK ENGINE
# FINAL TRADE FILTER
# ============================================================

# Bu modül:
# - sinyal seviyelerini doğrular
# - R/R oranını yeniden hesaplar
# - BTC rejim çatışmasını kontrol eder
# - günlük zarar limitini kontrol eder
# - pozisyon büyüklüğü hesaplar
#
# İşlem açmaz.
# PaperTrader portföy riskini ayrıca kontrol eder.


# ============================================================
# CONSTANTS
# ============================================================

MAX_FINAL_CONFIDENCE = 94.0

DEFAULT_RISK_PER_TRADE = 0.01
DEFAULT_MAX_DAILY_LOSS = 0.03

DEFAULT_MIN_CONFIDENCE = 60.0
DEFAULT_MIN_RR = 1.8

# Aşırı geniş stoplar kontrol dışı bırakılır.
# %10 üzerindeki stop mesafesi burada reddedilir.
MAX_STOP_DISTANCE_PERCENT = 10.0


# ============================================================
# HELPERS
# ============================================================

def _num(
    value,
    default=0.0,
):

    try:

        return float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return default


def _side(
    value,
):

    value = str(
        value or ""
    ).upper()

    if value in (
        "LONG",
        "BUY",
    ):

        return "LONG"

    if value in (
        "SHORT",
        "SELL",
    ):

        return "SHORT"

    return "WAIT"


# ============================================================
# R/R CALCULATION
# ============================================================

def calculate_rr(
    entry,
    stop,
    target,
):

    entry = _num(entry)
    stop = _num(stop)
    target = _num(target)

    if (
        entry <= 0
        or stop <= 0
        or target <= 0
    ):

        return 0.0

    risk = abs(
        entry - stop
    )

    reward = abs(
        target - entry
    )

    if risk <= 0:

        return 0.0

    return (
        reward
        /
        risk
    )


# ============================================================
# STOP DISTANCE
# ============================================================

def stop_distance_percent(
    entry,
    stop,
):

    entry = _num(entry)
    stop = _num(stop)

    if (
        entry <= 0
        or stop <= 0
    ):

        return 0.0

    return (
        abs(
            entry - stop
        )
        /
        entry
        *
        100.0
    )


# ============================================================
# SINGLE SIGNAL CHECK
# ============================================================

def validate_signal(
    signal,
    btc_regime="UNKNOWN",
    min_confidence=DEFAULT_MIN_CONFIDENCE,
    min_rr=DEFAULT_MIN_RR,
):

    if not isinstance(
        signal,
        dict,
    ):

        return (
            False,
            "INVALID_SIGNAL",
        )

    # ========================================================
    # DIRECTION
    # ========================================================

    direction = _side(
        signal.get(
            "direction"
        )
    )

    if direction == "WAIT":

        return (
            False,
            "NO_DIRECTION",
        )

    # ========================================================
    # BASIC VALUES
    # ========================================================

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

    if score <= 0:

        return (
            False,
            "INVALID_SCORE",
        )

    if confidence < min_confidence:

        return (
            False,
            "CONFIDENCE_TOO_LOW",
        )

    # ========================================================
    # PRICE LEVELS
    # ========================================================

    entry = _num(
        signal.get(
            "entry"
        )
    )

    stop = _num(
        signal.get(
            "stop"
        )
    )

    tp1 = _num(
        signal.get(
            "tp1"
        )
    )

    tp2 = _num(
        signal.get(
            "tp2"
        )
    )

    if entry <= 0:

        return (
            False,
            "INVALID_ENTRY",
        )

    if stop <= 0:

        return (
            False,
            "INVALID_STOP",
        )

    if (
        tp1 <= 0
        or tp2 <= 0
    ):

        return (
            False,
            "INVALID_TARGET",
        )

    # ========================================================
    # LONG LEVEL VALIDATION
    # ========================================================

    if direction == "LONG":

        if stop >= entry:

            return (
                False,
                "LONG_STOP_INVALID",
            )

        if tp1 <= entry:

            return (
                False,
                "LONG_TP1_INVALID",
            )

        if tp2 <= tp1:

            return (
                False,
                "LONG_TP2_INVALID",
            )

    # ========================================================
    # SHORT LEVEL VALIDATION
    # ========================================================

    if direction == "SHORT":

        if stop <= entry:

            return (
                False,
                "SHORT_STOP_INVALID",
            )

        if tp1 >= entry:

            return (
                False,
                "SHORT_TP1_INVALID",
            )

        if tp2 >= tp1:

            return (
                False,
                "SHORT_TP2_INVALID",
            )

    # ========================================================
    # STOP DISTANCE
    # ========================================================

    stop_percent = (
        stop_distance_percent(
            entry,
            stop,
        )
    )

    if stop_percent <= 0:

        return (
            False,
            "INVALID_STOP_DISTANCE",
        )

    if (
        stop_percent
        >
        MAX_STOP_DISTANCE_PERCENT
    ):

        return (
            False,
            "STOP_TOO_WIDE",
        )

    # ========================================================
    # RECALCULATE R/R
    # ========================================================

    calculated_rr = calculate_rr(
        entry,
        stop,
        tp2,
    )

    if calculated_rr < min_rr:

        return (
            False,
            "RISK_REWARD_TOO_LOW",
        )

    # Sinyaldeki R/R değerini
    # hesaplanan gerçek değerle değiştir.
    signal["rr"] = round(
        calculated_rr,
        3,
    )

    # ========================================================
    # BTC REGIME
    # ========================================================

    regime = _side(
        btc_regime
    )

    btc_conflict = (
        regime in (
            "LONG",
            "SHORT",
        )
        and
        regime != direction
    )

    signal["btc_conflict"] = (
        btc_conflict
    )

    # ========================================================
    # VALID
    # ========================================================

    return (
        True,
        "VALID",
    )


# ============================================================
# FINAL SIGNAL
# ============================================================

def get_final_signal(
    signals,
    btc_regime="UNKNOWN",
    min_confidence=DEFAULT_MIN_CONFIDENCE,
    min_rr=DEFAULT_MIN_RR,
):

    if not signals:

        return None

    valid = []

    for signal in signals:

        # Kopya üzerinde çalış.
        item = dict(
            signal
        )

        ok, reason = validate_signal(
            item,
            btc_regime=btc_regime,
            min_confidence=min_confidence,
            min_rr=min_rr,
        )

        if not ok:

            continue

        item[
            "risk_status"
        ] = "APPROVED"

        item[
            "risk_reason"
        ] = reason

        valid.append(
            item
        )

    if not valid:

        return None

    # ========================================================
    # RANKING
    # ========================================================

    def ranking(
        signal
    ):

        confidence = _num(
            signal.get(
                "confidence"
            )
        )

        score = _num(
            signal.get(
                "score"
            )
        )

        rr = _num(
            signal.get(
                "rr"
            )
        )

        # BTC ters yöndeyse tamamen
        # yasaklamıyoruz fakat ciddi
        # bir kalite cezası uyguluyoruz.
        conflict_penalty = (

            8.0

            if signal.get(
                "btc_conflict",
                False,
            )

            else 0.0
        )

        return (

            confidence * 0.50

            +

            score * 4.0

            +

            min(
                max(rr, 0.0),
                4.0,
            ) * 5.0

            -

            conflict_penalty
        )

    best = max(
        valid,
        key=ranking,
    )

    # ========================================================
    # FINAL CONFIDENCE
    # ========================================================

    confidence = _num(
        best.get(
            "confidence"
        )
    )

    if best.get(
        "btc_conflict",
        False,
    ):

        confidence -= 8.0

    confidence = max(
        0.0,
        min(
            MAX_FINAL_CONFIDENCE,
            confidence,
        ),
    )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    result = dict(
        best
    )

    result[
        "confidence"
    ] = round(
        confidence,
        1,
    )

    result[
        "risk_status"
    ] = "APPROVED"

    result[
        "execution_ready"
    ] = True

    return result


# ============================================================
# POSITION SIZE
# ============================================================

def calculate_position_size(
    balance,
    entry,
    stop,
    risk_per_trade=DEFAULT_RISK_PER_TRADE,
):

    balance = _num(
        balance
    )

    entry = _num(
        entry
    )

    stop = _num(
        stop
    )

    risk_per_trade = _num(
        risk_per_trade,
        DEFAULT_RISK_PER_TRADE,
    )

    if (
        balance <= 0
        or entry <= 0
        or stop <= 0
    ):

        return 0.0

    if risk_per_trade <= 0:

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
# RISK AMOUNT
# ============================================================

def calculate_risk_amount(
    balance,
    risk_per_trade=DEFAULT_RISK_PER_TRADE,
):

    balance = _num(
        balance
    )

    risk_per_trade = _num(
        risk_per_trade,
        DEFAULT_RISK_PER_TRADE,
    )

    if (
        balance <= 0
        or risk_per_trade <= 0
    ):

        return 0.0

    return (
        balance
        *
        risk_per_trade
    )


# ============================================================
# DAILY LOSS CHECK
# ============================================================

def daily_loss_allowed(
    starting_balance,
    current_balance,
    max_daily_loss=DEFAULT_MAX_DAILY_LOSS,
):

    starting_balance = _num(
        starting_balance
    )

    current_balance = _num(
        current_balance
    )

    max_daily_loss = _num(
        max_daily_loss,
        DEFAULT_MAX_DAILY_LOSS,
    )

    if starting_balance <= 0:

        return False

    if max_daily_loss <= 0:

        return False

    loss = (
        starting_balance
        -
        current_balance
    )

    # Hesap kârda veya başa başsa
    # günlük zarar limiti ihlal edilmez.
    if loss <= 0:

        return True

    loss_ratio = (
        loss
        /
        starting_balance
    )

    # Limite ulaşıldığında yeni işlem yok.
    return (
        loss_ratio
        <
        max_daily_loss
    )


# ============================================================
# DAILY LOSS AMOUNT
# ============================================================

def daily_loss_amount(
    starting_balance,
    current_balance,
):

    starting_balance = _num(
        starting_balance
    )

    current_balance = _num(
        current_balance
    )

    if starting_balance <= 0:

        return 0.0

    loss = (
        starting_balance
        -
        current_balance
    )

    return max(
        0.0,
        loss,
    )


# ============================================================
# DAILY LOSS PERCENT
# ============================================================

def daily_loss_percent(
    starting_balance,
    current_balance,
):

    starting_balance = _num(
        starting_balance
    )

    current_balance = _num(
        current_balance
    )

    if starting_balance <= 0:

        return 0.0

    loss = daily_loss_amount(
        starting_balance,
        current_balance,
    )

    return (
        loss
        /
        starting_balance
        *
        100.0
    )
