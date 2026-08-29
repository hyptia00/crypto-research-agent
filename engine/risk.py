# ============================================================
# CRYPTO RESEARCH AGENT
# RISK ENGINE
# ============================================================

from config import (
    MAX_RISK_PERCENT,
    MIN_RR,
)


# ============================================================
# SETTINGS
# ============================================================

MAX_POSITION_PERCENT = 100.0

MAX_STOP_DISTANCE_PERCENT = 10.0

MIN_STOP_DISTANCE_PERCENT = 0.10


# ============================================================
# HELPERS
# ============================================================

def _number(value, default=None):

    try:
        return float(value)

    except (
        TypeError,
        ValueError,
    ):

        return default


# ============================================================
# RISK DISTANCE
# ============================================================

def calculate_risk_distance(
    entry,
    stop,
):

    entry = _number(entry)
    stop = _number(stop)

    if entry is None or stop is None:
        return None

    return abs(
        entry - stop
    )


def calculate_risk_percent(
    entry,
    stop,
):

    entry = _number(entry)
    stop = _number(stop)

    if (
        entry is None
        or stop is None
        or entry <= 0
    ):
        return None

    return (
        abs(entry - stop)
        / entry
    ) * 100


# ============================================================
# R/R
# ============================================================

def calculate_rr(
    entry,
    stop,
    target,
):

    entry = _number(entry)
    stop = _number(stop)
    target = _number(target)

    if (
        entry is None
        or stop is None
        or target is None
    ):
        return None

    risk = abs(
        entry - stop
    )

    reward = abs(
        target - entry
    )

    if risk <= 0:
        return None

    return reward / risk


# ============================================================
# POSITION SIZE
# ============================================================

def calculate_position_size(
    balance,
    entry,
    stop,
    risk_percent=None,
):

    balance = _number(balance)
    entry = _number(entry)
    stop = _number(stop)

    if (
        balance is None
        or entry is None
        or stop is None
        or balance <= 0
        or entry <= 0
    ):
        return 0.0

    if risk_percent is None:
        risk_percent = MAX_RISK_PERCENT

    risk_percent = _number(
        risk_percent,
        MAX_RISK_PERCENT
    )

    if risk_percent <= 0:
        return 0.0

    risk_amount = (
        balance
        * risk_percent
        / 100
    )

    stop_distance = abs(
        entry - stop
    )

    if stop_distance <= 0:
        return 0.0

    quantity = (
        risk_amount
        / stop_distance
    )

    return quantity


# ============================================================
# NOTIONAL
# ============================================================

def calculate_notional(
    quantity,
    entry,
):

    quantity = _number(
        quantity
    )

    entry = _number(
        entry
    )

    if (
        quantity is None
        or entry is None
    ):
        return 0.0

    return quantity * entry


# ============================================================
# POSITION PERCENT
# ============================================================

def calculate_position_percent(
    balance,
    notional,
):

    balance = _number(
        balance
    )

    notional = _number(
        notional
    )

    if (
        balance is None
        or notional is None
        or balance <= 0
    ):
        return 0.0

    return (
        notional
        / balance
    ) * 100


# ============================================================
# VALIDATE DIRECTION
# ============================================================

def validate_direction(
    signal
):

    side = signal.get(
        "side"
    )

    entry = _number(
        signal.get("entry")
    )

    stop = _number(
        signal.get("stop")
    )

    tp1 = _number(
        signal.get("tp1")
    )

    if (
        entry is None
        or stop is None
        or tp1 is None
    ):
        return False

    if side in (
        "LONG",
        "BUY",
    ):

        if stop >= entry:
            return False

        if tp1 <= entry:
            return False

        return True

    if side == "SHORT":

        if stop <= entry:
            return False

        if tp1 >= entry:
            return False

        return True

    return False


# ============================================================
# VALIDATE RISK
# ============================================================

def validate_risk(
    signal
):

    if not signal:
        return False

    if not validate_direction(
        signal
    ):
        return False

    entry = _number(
        signal.get("entry")
    )

    stop = _number(
        signal.get("stop")
    )

    tp1 = _number(
        signal.get("tp1")
    )

    risk_percent = (
        calculate_risk_percent(
            entry,
            stop
        )
    )

    if risk_percent is None:
        return False

    # Çok dar SL
    if risk_percent < MIN_STOP_DISTANCE_PERCENT:
        return False

    # Aşırı geniş SL
    if risk_percent > MAX_STOP_DISTANCE_PERCENT:
        return False

    rr = calculate_rr(
        entry,
        stop,
        tp1
    )

    if rr is None:
        return False

    if rr < MIN_RR:
        return False

    return True


# ============================================================
# BUILD RISK DATA
# ============================================================

def build_risk_data(
    signal,
    balance,
):

    entry = _number(
        signal.get("entry")
    )

    stop = _number(
        signal.get("stop")
    )

    tp1 = _number(
        signal.get("tp1")
    )

    tp2 = _number(
        signal.get("tp2")
    )

    if (
        entry is None
        or stop is None
    ):
        return None

    risk_distance = (
        calculate_risk_distance(
            entry,
            stop
        )
    )

    risk_percent = (
        calculate_risk_percent(
            entry,
            stop
        )
    )

    rr_tp1 = (
        calculate_rr(
            entry,
            stop,
            tp1
        )
        if tp1 is not None
        else None
    )

    rr_tp2 = (
        calculate_rr(
            entry,
            stop,
            tp2
        )
        if tp2 is not None
        else None
    )

    quantity = (
        calculate_position_size(
            balance,
            entry,
            stop
        )
    )

    notional = (
        calculate_notional(
            quantity,
            entry
        )
    )

    position_percent = (
        calculate_position_percent(
            balance,
            notional
        )
    )

    return {

        "balance":
            balance,

        "risk_percent":
            risk_percent,

        "risk_distance":
            risk_distance,

        "risk_amount":
            balance
            * MAX_RISK_PERCENT
            / 100,

        "quantity":
            quantity,

        "notional":
            notional,

        "position_percent":
            position_percent,

        "rr_tp1":
            rr_tp1,

        "rr_tp2":
            rr_tp2,

    }


# ============================================================
# APPLY RISK
# ============================================================

def apply_risk(
    signal,
    balance,
):

    """
    Sinyali risk kontrolünden geçirir.

    Başarılıysa sinyale:

        quantity
        notional
        risk_amount
        risk_percent
        R/R

    ekler.
    """

    if not signal:
        return None

    if signal.get(
        "side"
    ) == "WAIT":

        return None

    if not validate_risk(
        signal
    ):

        return None

    risk_data = (
        build_risk_data(
            signal,
            balance
        )
    )

    if risk_data is None:
        return None

    # --------------------------------------------------------
    # MAX POSITION CHECK
    # --------------------------------------------------------

    if (
        risk_data[
            "position_percent"
        ]
        > MAX_POSITION_PERCENT
    ):

        return None

    result = dict(
        signal
    )

    result[
        "quantity"
    ] = risk_data[
        "quantity"
    ]

    result[
        "notional"
    ] = risk_data[
        "notional"
    ]

    result[
        "risk_amount"
    ] = risk_data[
        "risk_amount"
    ]

    result[
        "risk_percent"
    ] = risk_data[
        "risk_percent"
    ]

    result[
        "rr_tp1"
    ] = risk_data[
        "rr_tp1"
    ]

    result[
        "rr_tp2"
    ] = risk_data[
        "rr_tp2"
    ]

    result[
        "position_percent"
    ] = risk_data[
        "position_percent"
    ]

    result[
        "risk_status"
    ] = "APPROVED"

    return result


# ============================================================
# RISK REJECTION REASON
# ============================================================

def risk_rejection_reason(
    signal
):

    if not signal:
        return "SIGNAL_EMPTY"

    if signal.get(
        "side"
    ) == "WAIT":

        return "SIGNAL_WAIT"

    if not validate_direction(
        signal
    ):

        return "INVALID_DIRECTION_OR_LEVELS"

    entry = _number(
        signal.get("entry")
    )

    stop = _number(
        signal.get("stop")
    )

    tp1 = _number(
        signal.get("tp1")
    )

    risk_percent = (
        calculate_risk_percent(
            entry,
            stop
        )
    )

    if risk_percent is None:
        return "INVALID_RISK"

    if risk_percent < MIN_STOP_DISTANCE_PERCENT:
        return "STOP_TOO_TIGHT"

    if risk_percent > MAX_STOP_DISTANCE_PERCENT:
        return "STOP_TOO_WIDE"

    rr = calculate_rr(
        entry,
        stop,
        tp1
    )

    if rr is None:
        return "INVALID_RR"

    if rr < MIN_RR:
        return "RR_TOO_LOW"

    return "UNKNOWN"


# ============================================================
# RISK REPORT
# ============================================================

def risk_report(
    signal
):

    if not signal:
        return "NO SIGNAL"

    return (
        f"Risk={signal.get('risk_percent', 0):.2f}% | "
        f"Position={signal.get('position_percent', 0):.2f}% | "
        f"Qty={signal.get('quantity', 0):.6f} | "
        f"R/R TP1={signal.get('rr_tp1', 0):.2f} | "
        f"R/R TP2={signal.get('rr_tp2', 0):.2f} | "
        f"Status={signal.get('risk_status', 'N/A')}"
    )
