# ============================================================
# CRYPTO RESEARCH AGENT
# CENTRAL ORCHESTRATOR
# ============================================================

"""
ANA AGENT

Bu dosya bütün strateji motorlarını yönetir.

MİMARİ:

                    ┌──────────────┐
                    │  DATA ENGINE │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ↓            ↓            ↓
         INDICATORS    STRUCTURE     MARKET DATA
              │            │            │
              └────────────┼────────────┘
                           ↓
                 ┌──────────────────┐
                 │  STRATEGY ENGINE │
                 └────────┬─────────┘
                          │
             ┌────────────┼────────────┐
             ↓            ↓            ↓
          FUTURES        SPOT       SCALPING
             │            │            │
             └────────────┼────────────┘
                          ↓
                  SIGNAL AGGREGATOR
                          ↓
                    RISK FILTER
                          ↓
                     FINAL SIGNAL

Ana prensip:

1. Veri topla
2. Teknik göstergeleri hesapla
3. Market structure çıkar
4. Futures analiz et
5. Spot analiz et
6. Scalping analiz et
7. Sinyalleri karşılaştır
8. Çakışan / zayıf sinyalleri ele
9. Risk/RR kontrolü yap
10. En kaliteli sinyali üret

Bu dosya doğrudan emir göndermez.
Execution katmanı daha sonra eklenecek.
"""


# ============================================================
# IMPORTS
# ============================================================

import traceback
from datetime import datetime


# ------------------------------------------------------------
# MARKET MODULES
# ------------------------------------------------------------

try:
    from market.data_engine import (
        get_klines
    )
except Exception:
    get_klines = None


try:
    from market.indicators import (
        calculate_indicators
    )
except Exception:
    calculate_indicators = None


try:
    from market.structure import (
        analyze_structure
    )
except Exception:
    analyze_structure = None


# ------------------------------------------------------------
# STRATEGIES
# ------------------------------------------------------------

try:
    from strategies.scalping import (
        analyze_scalping
    )
except Exception:
    analyze_scalping = None


try:
    from strategies.futures import (
        analyze_futures
    )
except Exception:
    analyze_futures = None


try:
    from strategies.spot import (
        analyze_spot
    )
except Exception:
    analyze_spot = None


# ============================================================
# CONFIGURATION
# ============================================================

MAIN_COINS = [

    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",

    "DOTUSDT",
    "NEARUSDT",
    "JUPUSDT",
    "MOVRUSDT",
    "TNSRUSDT",
]


# ------------------------------------------------------------
# DATA LIMITS
# ------------------------------------------------------------

LIMIT_15M = 300

LIMIT_5M = 300

LIMIT_1M = 300

LIMIT_1H = 300

LIMIT_4H = 300


# ============================================================
# SCORE THRESHOLDS
# ============================================================

MIN_FUTURES_SCORE = 7

MIN_SPOT_SCORE = 7

MIN_SCALPING_SCORE = 7


# ============================================================
# MARKET DATA
# ============================================================

def load_timeframes(symbol):

    """
    Bir coin için bütün gerekli timeframe'leri toplar.

    4H:
        Ana trend

    1H:
        Orta vadeli trend

    15M:
        Setup

    5M:
        Confirmation

    1M:
        Entry
    """

    result = {}

    timeframes = {

        "4h": LIMIT_4H,

        "1h": LIMIT_1H,

        "15m": LIMIT_15M,

        "5m": LIMIT_5M,

        "1m": LIMIT_1M,
    }

    if get_klines is None:

        return result

    for timeframe, limit in timeframes.items():

        try:

            data = get_klines(
                symbol,
                timeframe,
                limit
            )

            if data:

                result[timeframe] = data

        except Exception as e:

            print(
                f"{symbol} {timeframe} "
                f"VERI HATASI: {e}"
            )

    return result


# ============================================================
# INDICATORS
# ============================================================

def calculate_all_indicators(data):

    """
    Her timeframe için indikatörleri hesaplar.
    """

    result = {}

    if calculate_indicators is None:

        return result

    for timeframe, candles in data.items():

        try:

            result[timeframe] = (
                calculate_indicators(
                    candles
                )
            )

        except Exception as e:

            print(
                f"{timeframe} "
                f"INDICATOR HATASI: {e}"
            )

            result[timeframe] = {}

    return result


# ============================================================
# MARKET STRUCTURE
# ============================================================

def calculate_all_structures(data):

    """
    Her timeframe için market structure çıkarır.

    Beklenen yapılar:

    - BOS
    - CHoCH
    - MSB
    - Liquidity Sweep
    - FVG
    - Order Block
    - Displacement
    - Swing High
    - Swing Low
    """

    result = {}

    if analyze_structure is None:

        return result

    for timeframe, candles in data.items():

        try:

            result[timeframe] = (
                analyze_structure(
                    candles
                )
            )

        except Exception as e:

            print(
                f"{timeframe} "
                f"STRUCTURE HATASI: {e}"
            )

            result[timeframe] = {}

    return result


# ============================================================
# BTC REGIME
# ============================================================

def determine_btc_regime(
    indicators,
    structures
):

    """
    BTC'nin genel piyasa rejimini belirler.

    LONG:
        Altcoin long işlemleri daha güvenli.

    SHORT:
        Short işlemler daha güvenli.

    NEUTRAL:
        Seçici davran.

    RISK_OFF:
        Yeni işlem açmak için çok daha sıkı filtre.
    """

    try:

        btc_4h = structures.get(
            "4h",
            {}
        )

        btc_1h = structures.get(
            "1h",
            {}
        )

        bias_4h = btc_4h.get(
            "bias",
            "NEUTRAL"
        )

        bias_1h = btc_1h.get(
            "bias",
            "NEUTRAL"
        )

        if (
            bias_4h in (
                "BULLISH",
                "WEAK_BULLISH"
            )
            and
            bias_1h in (
                "BULLISH",
                "WEAK_BULLISH"
            )
        ):

            return "LONG"

        if (
            bias_4h in (
                "BEARISH",
                "WEAK_BEARISH"
            )
            and
            bias_1h in (
                "BEARISH",
                "WEAK_BEARISH"
            )
        ):

            return "SHORT"

        return "NEUTRAL"

    except Exception:

        return "NEUTRAL"


# ============================================================
# SCALPING
# ============================================================

def run_scalping(
    symbol,
    data,
    indicators,
    structures
):

    if analyze_scalping is None:

        return {
            "signal": "UNAVAILABLE",
            "score": 0,
        }

    try:

        return analyze_scalping(

            symbol,

            data.get("15m", []),

            data.get("5m", []),

            data.get("1m", []),

            structures.get(
                "15m",
                {}
            ),

            structures.get(
                "5m",
                {}
            ),

            structures.get(
                "1m",
                {}
            ),

            indicators.get(
                "15m",
                {}
            ),

            indicators.get(
                "5m",
                {}
            ),

            indicators.get(
                "1m",
                {}),
        )

    except Exception as e:

        return {

            "signal": "ERROR",

            "score": 0,

            "reason": str(e),

        }


# ============================================================
# FUTURES
# ============================================================

def run_futures(
    symbol,
    data,
    indicators,
    structures,
    btc_regime
):

    if analyze_futures is None:

        return {
            "signal": "UNAVAILABLE",
            "score": 0,
        }

    try:

        return analyze_futures(

            symbol,

            data,

            indicators,

            structures,

            btc_regime,

        )

    except Exception as e:

        return {

            "signal": "ERROR",

            "score": 0,

            "reason": str(e),

        }


# ============================================================
# SPOT
# ============================================================

def run_spot(
    symbol,
    data,
    indicators,
    structures,
    btc_regime
):

    if analyze_spot is None:

        return {
            "signal": "UNAVAILABLE",
            "score": 0,
        }

    try:

        return analyze_spot(

            symbol,

            data,

            indicators,

            structures,

            btc_regime,

        )

    except Exception as e:

        return {

            "signal": "ERROR",

            "score": 0,

            "reason": str(e),

        }


# ============================================================
# SIGNAL QUALITY
# ============================================================

def signal_quality(signal):

    """
    Sinyalin genel kalitesini hesaplar.

    Skor dışında:

    - confidence
    - R/R
    - timeframe confirmation
    """

    if not signal:

        return 0

    score = 0

    raw_score = signal.get(
        "score",
        0
    )

    try:

        raw_score = float(
            raw_score
        )

    except Exception:

        raw_score = 0

    score += raw_score

    confidence = signal.get(
        "confidence",
        0
    )

    try:

        confidence = float(
            confidence
        )

    except Exception:

        confidence = 0

    score += (
        confidence / 20
    )

    rr = signal.get(
        "rr",
        0
    )

    try:

        rr = float(rr)

    except Exception:

        rr = 0

    if rr >= 2:

        score += 2

    if rr >= 2.5:

        score += 2

    return score


# ============================================================
# CONFLICT CHECK
# ============================================================

def check_conflict(
    futures,
    spot,
    scalping
):

    """
    Stratejiler birbirine ters mi bakıyor?

    Örneğin:

    Futures LONG
    Spot LONG
    Scalping LONG

    = güçlü uyum

    Futures LONG
    Spot WAIT
    Scalping SHORT

    = çatışma
    """

    signals = []

    for result in (
        futures,
        spot,
        scalping
    ):

        if not result:
            continue

        signal = result.get(
            "signal"
        )

        if signal in (
            "LONG",
            "SHORT"
        ):

            signals.append(
                signal
            )

    if not signals:

        return {
            "status": "NONE",
            "direction": None,
            "agreement": 0,
        }

    longs = signals.count(
        "LONG"
    )

    shorts = signals.count(
        "SHORT"
    )

    if longs > shorts:

        direction = "LONG"

        agreement = longs

    elif shorts > longs:

        direction = "SHORT"

        agreement = shorts

    else:

        return {
            "status": "CONFLICT",
            "direction": None,
            "agreement": 0,
        }

    if agreement == len(signals):

        status = "ALIGNED"

    else:

        status = "PARTIAL"

    return {

        "status": status,

        "direction": direction,

        "agreement": agreement,

    }


# ============================================================
# FINAL DECISION
# ============================================================

def final_decision(
    symbol,
    futures,
    spot,
    scalping,
    btc_regime
):

    """
    Bütün stratejileri tek sinyale dönüştürür.

    ÖNEMLİ:

    Tek bir indikatör işlem açtıramaz.

    En azından:

        Structure
        + Momentum
        + Risk/RR

    kombinasyonu gerekir.
    """

    conflict = check_conflict(
        futures,
        spot,
        scalping
    )

    candidates = []

    for name, result in (

        ("FUTURES", futures),

        ("SPOT", spot),

        ("SCALPING", scalping),

    ):

        if not result:
            continue

        signal = result.get(
            "signal"
        )

        if signal not in (
            "LONG",
            "SHORT"
        ):

            continue

        quality = signal_quality(
            result
        )

        candidates.append({

            "type": name,

            "signal": signal,

            "quality": quality,

            "score": result.get(
                "score",
                0
            ),

            "result": result,

        })

    if not candidates:

        return {

            "symbol": symbol,

            "signal": "WAIT",

            "confidence": 0,

            "reason":
                "Geçerli strateji sinyali yok",

            "btc_regime":
                btc_regime,

        }

    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

    candidates.sort(
        key=lambda x:
        x["quality"],
        reverse=True
    )

    best = candidates[0]

    direction = best[
        "signal"
    ]

    # --------------------------------------------------------
    # CONFLICT PROTECTION
    # --------------------------------------------------------

    if (
        conflict["status"]
        == "CONFLICT"
    ):

        return {

            "symbol": symbol,

            "signal": "WAIT",

            "confidence": 0,

            "reason":
                "Stratejiler yön konusunda çatışıyor",

            "btc_regime":
                btc_regime,

        }

    # --------------------------------------------------------
    # BTC REGIME FILTER
    # --------------------------------------------------------

    if btc_regime == "LONG":

        if direction == "SHORT":

            # Short tamamen yasak değil,
            # ancak ekstra teyit gerekir.

            if best["score"] < 8:

                return {

                    "symbol": symbol,

                   
