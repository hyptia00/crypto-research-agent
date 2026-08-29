# ============================================================
# RISK FILTER ENGINE
# ============================================================

from typing import Any, Dict, Optional


def _float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _direction(signal: Dict[str, Any]) -> str:
    direction = str(
        signal.get(
            "direction",
            signal.get("side", "")
        )
    ).upper()

    if direction == "BUY":
        return "LONG"

    if direction == "SELL":
        return "SHORT"

    return direction


def calculate_risk_reward(
    entry: float,
    stop: float,
    target: float,
    direction: str,
) -> float:

    entry = _float(entry)
    stop = _float(stop)
    target = _float(target)

    if entry <= 0 or stop <= 0 or target <= 0:
        return 0.0

    direction = direction.upper()

    if direction == "LONG":

        risk = entry - stop
        reward = target - entry

    elif direction == "SHORT":

        risk = stop - entry
        reward = entry - target

    else:
        return 0.0

    if risk <= 0:
        return 0.0

    return reward / risk


def validate_signal(
    signal: Dict[str, Any],
    btc_regime: Optional[str] = None,
    min_confidence: float = 65.0,
    min_rr: float = 1.8,
) -> Dict[str, Any]:

    if not isinstance(signal, dict):

        return {
            "approved": False,
            "reason": "INVALID_SIGNAL",
        }

    symbol = str(
        signal.get("symbol", "")
    ).upper()

    direction = _direction(signal)

    entry = _float(
        signal.get(
            "entry",
            signal.get("price")
        )
    )

    stop = _float(
        signal.get("stop")
    )

    tp1 = _float(
        signal.get("tp1")
    )

    tp2 = _float(
        signal.get("tp2")
    )

    confidence = _float(
        signal.get("confidence")
    )

    score = _float(
        signal.get("score")
    )

    # --------------------------------------------------------
    # BASIC VALIDATION
    # --------------------------------------------------------

    if not symbol:
        return {
            "approved": False,
            "reason": "MISSING_SYMBOL",
        }

    if direction not in ("LONG", "SHORT"):
        return {
            "approved": False,
            "reason": "INVALID_DIRECTION",
            "symbol": symbol,
        }

    if entry <= 0:
        return {
            "approved": False,
            "reason": "INVALID_ENTRY",
            "symbol": symbol,
        }

    if stop <= 0:
        return {
            "approved": False,
            "reason": "MISSING_STOP",
            "symbol": symbol,
        }

    if tp1 <= 0 and tp2 <= 0:
        return {
            "approved": False,
            "reason": "MISSING_TARGET",
            "symbol": symbol,
        }

    # --------------------------------------------------------
    # STOP LOCATION
    # --------------------------------------------------------

    if direction == "LONG" and stop >= entry:

        return {
            "approved": False,
            "reason": "LONG_STOP_INVALID",
            "symbol": symbol,
        }

    if direction == "SHORT" and stop <= entry:

        return {
            "approved": False,
            "reason": "SHORT_STOP_INVALID",
            "symbol": symbol,
        }

    # --------------------------------------------------------
    # TARGET
    # --------------------------------------------------------

    target = tp2 if tp2 > 0 else tp1

    if direction == "LONG" and target <= entry:

        return {
            "approved": False,
            "reason": "LONG_TARGET_INVALID",
            "symbol": symbol,
        }

    if direction == "SHORT" and target >= entry:

        return {
            "approved": False,
            "reason": "SHORT_TARGET_INVALID",
            "symbol": symbol,
        }

    # --------------------------------------------------------
    # RISK / REWARD
    # --------------------------------------------------------

    rr = calculate_risk_reward(
        entry,
        stop,
        target,
        direction,
    )

    if rr < min_rr:

        return {
            "approved": False,
            "reason": "RR_TOO_LOW",
            "symbol": symbol,
            "rr": round(rr, 2),
            "required_rr": min_rr,
        }

    # --------------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------------

    if confidence < min_confidence:

        return {
            "approved": False,
            "reason": "CONFIDENCE_TOO_LOW",
            "symbol": symbol,
            "confidence": confidence,
            "required_confidence":
                min_confidence,
        }

    # --------------------------------------------------------
    # BTC REGIME FILTER
    # --------------------------------------------------------

    regime = str(
        btc_regime
        or signal.get("btc_regime", "UNKNOWN")
    ).upper()

    # BTC LONG rejimdeyse SHORT için
    # daha güçlü teyit gerekir.
    if regime == "LONG" and direction == "SHORT":

        if confidence < 75:

            return {
                "approved": False,
                "reason":
                    "BTC_REGIME_AGAINST_SHORT",
                "symbol": symbol,
                "confidence": confidence,
                "btc_regime": regime,
            }

    # BTC SHORT rejimdeyse LONG için
    # daha güçlü teyit gerekir.
    if regime == "SHORT" and direction == "LONG":

        if confidence < 75:

            return {
                "approved": False,
                "reason":
                    "BTC_REGIME_AGAINST_LONG",
                "symbol": symbol,
                "confidence": confidence,
                "btc_regime": regime,
            }

    # --------------------------------------------------------
    # APPROVED
    # --------------------------------------------------------

    result = dict(signal)

    result["symbol"] = symbol
    result["direction"] = direction
    result["entry"] = entry
    result["stop"] = stop
    result["tp1"] = tp1
    result["tp2"] = tp2
    result["rr"] = round(rr, 2)
    result["confidence"] = round(
        confidence,
        1
    )
    result["risk_approved"] = True
    result["btc_regime"] = regime

    return {
        "approved": True,
        "reason": "RISK_CHECK_PASSED",
        "signal": result,
    }


def filter_signals(
    signals,
    btc_regime: Optional[str] = None,
    min_confidence: float = 65.0,
    min_rr: float = 1.8,
):

    approved = []
    rejected = []

    for signal in signals or []:

        result = validate_signal(
            signal,
            btc_regime=btc_regime,
            min_confidence=min_confidence,
            min_rr=min_rr,
        )

        if result["approved"]:

            approved.append(
                result["signal"]
            )

        else:

            rejected.append(result)

    return {
        "approved": approved,
        "rejected": rejected,
    }


def get_final_signal(
    signals,
    btc_regime: Optional[str] = None,
    min_confidence: float = 65.0,
    min_rr: float = 1.8,
):

    result = filter_signals(
        signals,
        btc_regime=btc_regime,
        min_confidence=min_confidence,
        min_rr=min_rr,
    )

    if not result["approved"]:
        return None

    # En yüksek güven + RR kombinasyonu
    ranked = sorted(
        result["approved"],
        key=lambda x: (
            _float(
                x.get("confidence")
            ),
            _float(
                x.get("rr")
            ),
        ),
        reverse=True,
    )

    return ranked[0]
