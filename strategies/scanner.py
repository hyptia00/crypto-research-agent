# ============================================================
# CRYPTO RESEARCH AGENT
# OPPORTUNITY SCANNER
# ============================================================

"""
OPPORTUNITY SCANNER

Görevi:

1. Binance USDT marketlerini keşfetmek
2. Likidite filtresi uygulamak
3. Ana coinleri ayrı tutmak
4. Hareketlilik / hacim / momentum adaylarını bulmak
5. Adayları teknik analiz motorlarına göndermek
6. Futures / Spot / Scalping sonuçlarını toplamak
7. En kaliteli fırsatları sıralamak

ANA COINLER:
    BTC
    ETH
    SOL
    BNB
    XRP
    DOT
    NEAR
    JUP
    MOVR
    TNSR

Bunların dışında yeni coinler de aranır.

ÖNEMLİ:
Bu modül emir göndermez.
Sadece araştırma ve aday üretir.
"""


# ============================================================
# IMPORTS
# ============================================================

from datetime import datetime


# ============================================================
# DATA ENGINE
# ============================================================

try:

    from market.data_engine import (
        discover_symbols,
        get_spot_klines,
        get_24h_ticker,
    )

except Exception:

    discover_symbols = None
    get_spot_klines = None
    get_24h_ticker = None


# ============================================================
# INDICATORS
# ============================================================

try:

    from market.indicators import (
        calculate_indicators,
    )

except Exception:

    calculate_indicators = None


# ============================================================
# STRUCTURE
# ============================================================

try:

    from market.structure import (
        analyze_structure,
        structure_bias,
    )

except Exception:

    analyze_structure = None
    structure_bias = None


# ============================================================
# STRATEGIES
# ============================================================

try:

    from strategies.futures import (
        analyze_futures,
    )

except Exception:

    analyze_futures = None


try:

    from strategies.spot import (
        analyze_spot,
    )

except Exception:

    analyze_spot = None


try:

    from strategies.scalping import (
        analyze_scalping,
    )

except Exception:

    analyze_scalping = None


# ============================================================
# CONFIG
# ============================================================

CORE_SYMBOLS = [

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
# SCANNER LIMITS
# ------------------------------------------------------------

MAX_DISCOVERY = 100

MAX_ANALYSIS = 30

MAX_RESULTS = 15


# ------------------------------------------------------------
# LIQUIDITY
# ------------------------------------------------------------

MIN_VOLUME_USDT = 10_000_000

MIN_PRICE = 0.0001


# ------------------------------------------------------------
# MOMENTUM
# ------------------------------------------------------------

MOMENTUM_LOOKBACK = 20

MIN_MOMENTUM = 2.0


# ------------------------------------------------------------
# VOLUME
# ------------------------------------------------------------

MIN_VOLUME_RATIO = 1.0

STRONG_VOLUME_RATIO = 1.5


# ------------------------------------------------------------
# SCORE
# ------------------------------------------------------------

MIN_CANDIDATE_SCORE = 4

MIN_SIGNAL_SCORE = 7


# ============================================================
# HELPERS
# ============================================================

def safe_float(
    value,
    default=0.0
):

    try:

        return float(value)

    except (
        TypeError,
        ValueError
    ):

        return default


# ============================================================
# PRICE CHANGE
# ============================================================

def calculate_change(
    candles,
    periods=MOMENTUM_LOOKBACK
):

    if not candles:
        return 0.0

    if len(candles) <= periods:
        return 0.0

    old_price = safe_float(
        candles[
            -periods - 1
        ].get("close")
    )

    current_price = safe_float(
        candles[
            -1
        ].get("close")
    )

    if old_price <= 0:
        return 0.0

    return (
        (
            current_price
            - old_price
        )
        / old_price
    ) * 100


# ============================================================
# VOLUME RATIO
# ============================================================

def calculate_volume_ratio(
    candles,
    lookback=20
):

    if not candles:
        return 0.0

    if len(candles) < 2:
        return 0.0

    current = safe_float(
        candles[-1].get(
            "volume"
        )
    )

    previous = [

        safe_float(
            candle.get(
                "volume"
            )
        )

        for candle
        in candles[
            -lookback - 1:-1
        ]

    ]

    previous = [
        x for x in previous
        if x > 0
    ]

    if not previous:
        return 0.0

    average = (
        sum(previous)
        / len(previous)
    )

    if average <= 0:
        return 0.0

    return (
        current
        / average
    )


# ============================================================
# CANDIDATE SCORE
# ============================================================

def calculate_candidate_score(
    candles,
    indicators,
    structure
):

    score = 0

    reasons = []

    # ========================================================
    # MOMENTUM
    # ========================================================

    momentum = calculate_change(
        candles
    )

    if momentum >= MIN_MOMENTUM:

        score += 1

        reasons.append(
            "Pozitif momentum"
        )

    elif momentum <= -MIN_MOMENTUM:

        score += 1

        reasons.append(
            "Güçlü negatif momentum"
        )


    # ========================================================
    # VOLUME
    # ========================================================

    volume_ratio = (
        calculate_volume_ratio(
            candles
        )
    )

    if volume_ratio >= STRONG_VOLUME_RATIO:

        score += 2

        reasons.append(
            "Güçlü hacim artışı"
        )

    elif volume_ratio >= MIN_VOLUME_RATIO:

        score += 1

        reasons.append(
            "Hacim ortalamanın üzerinde"
        )


    # ========================================================
    # STRUCTURE
    # ========================================================

    if structure:

        bias = (
            structure.get(
                "structure",
                {}
            ).get(
                "bias",
                "SIDEWAYS"
            )
        )

        if bias in (
            "BULLISH",
            "WEAK_BULLISH"
        ):

            score += 2

            reasons.append(
                "Bullish market structure"
            )

        elif bias in (
            "BEARISH",
            "WEAK_BEARISH"
        ):

            score += 2

            reasons.append(
                "Bearish market structure"
            )


        # ----------------------------------------------------
        # MSB
        # ----------------------------------------------------

        if structure.get(
            "msb"
        ):

            score += 2

            reasons.append(
                "MSB bulundu"
            )


        # ----------------------------------------------------
        # LIQUIDITY
        # ----------------------------------------------------

        if structure.get(
            "liquidity_sweeps"
        ):

            score += 2

            reasons.append(
                "Liquidity sweep bulundu"
            )


        # ----------------------------------------------------
        # FVG
        # ----------------------------------------------------

        if structure.get(
            "fvg"
        ):

            score += 1

            reasons.append(
                "FVG bulundu"
            )


        # ----------------------------------------------------
        # ORDER BLOCK
        # ----------------------------------------------------

        if structure.get(
            "order_blocks"
        ):

            score += 1

            reasons.append(
                "Order Block bulundu"
            )


        # ----------------------------------------------------
        # DISPLACEMENT
        # ----------------------------------------------------

        if structure.get(
            "displacement"
        ):

            score += 1

            reasons.append(
                "Displacement bulundu"
            )


    return {

        "score":
            score,

        "momentum":
            momentum,

        "volume_ratio":
            volume_ratio,

        "reasons":
            reasons,

    }


# ============================================================
# MARKET DISCOVERY
# ============================================================

def discover_candidates():

    """
    Binance'tan likit USDT marketlerini keşfeder.

    Ana coinler discovery'den bağımsız tutulur.
    """

    if discover_symbols is None:

        return []

    try:

        symbols = discover_symbols(

            max_symbols=
                MAX_DISCOVERY,

            min_volume=
                MIN_VOLUME_USDT,

        )

    except Exception as e:

        print(
            "DISCOVERY HATASI:",
            e
        )

        return []


    # --------------------------------------------------------
    # CORE COINS REMOVE
    # --------------------------------------------------------

    candidates = [

        symbol

        for symbol
        in symbols

        if symbol
        not in CORE_SYMBOLS

    ]


    return candidates[
        :MAX_ANALYSIS
    ]


# ============================================================
# ANALYZE CANDIDATE
# ============================================================

def analyze_candidate(
    symbol
):

    """
    Tek bir yeni coin için
    ilk fırsat taraması.
    """

    if get_spot_klines is None:

        return None

    try:

        # ----------------------------------------------------
        # 4H
        # ----------------------------------------------------

        candles_4h = (
            get_spot_klines(
                symbol,
                "4h",
                200
            )
        )

        if not candles_4h:

            return None


        # ----------------------------------------------------
        # 1H
        # ----------------------------------------------------

        candles_1h = (
            get_spot_klines(
                symbol,
                "1h",
                200
            )
        )

        if not candles_1h:

            return None


        # ----------------------------------------------------
        # 15M
        # ----------------------------------------------------

        candles_15m = (
            get_spot_klines(
                symbol,
                "15m",
                200
            )
        )

        if not candles_15m:

            return None


        # ----------------------------------------------------
        # INDICATORS
        # ----------------------------------------------------

        indicators_4h = {}

        indicators_1h = {}

        indicators_15m = {}


        if calculate_indicators:

            indicators_4h = (
                calculate_indicators(
                    candles_4h
                )
            )

            indicators_1h = (
                calculate_indicators(
                    candles_1h
                )
            )

            indicators_15m = (
                calculate_indicators(
                    candles_15m
                )
            )


        # ----------------------------------------------------
        # STRUCTURE
        # ----------------------------------------------------

        structure_4h = {}

        structure_1h = {}

        structure_15m = {}


        if analyze_structure:

            structure_4h = (
                analyze_structure(
                    candles_4h
                )
            )

            structure_1h = (
                analyze_structure(
                    candles_1h
                )
            )

            structure_15m = (
                analyze_structure(
                    candles_15m
                )
            )


        # ----------------------------------------------------
        # SCORE
        # ----------------------------------------------------

        score_data = (
            calculate_candidate_score(

                candles_15m,

                indicators_15m,

                structure_15m,

            )
        )


        # ----------------------------------------------------
        # TREND
        # ----------------------------------------------------

        trend_4h = (
            structure_4h
            .get(
                "structure",
                {}
            )
            .get(
                "bias",
                "SIDEWAYS"
            )
        )

        trend_1h = (
            structure_1h
            .get(
                "structure",
                {}
            )
            .get(
                "bias",
                "SIDEWAYS"
            )
        )

        trend_15m = (
            structure_15m
            .get(
                "structure",
                {}
            )
            .get(
                "bias",
                "SIDEWAYS"
            )
        )


        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

        return {

            "symbol":
                symbol,

            "score":
                score_data["score"],

            "momentum":
                score_data["momentum"],

            "volume_ratio":
                score_data[
                    "volume_ratio"
                ],

            "trend_4h":
                trend_4h,

            "trend_1h":
                trend_1h,

            "trend_15m":
                trend_15m,

            "reasons":
                score_data["reasons"],

            "data":
                {

                    "4h":
                        candles_4h,

                    "1h":
                        candles_1h,

                    "15m":
                        candles_15m,

                },

            "indicators":
                {

                    "4h":
                        indicators_4h,

                    "1h":
                        indicators_1h,

                    "15m":
                        indicators_15m,

                },

            "structures":
                {

                    "4h":
                        structure_4h,

                    "1h":
                        structure_1h,

                    "15m":
                        structure_15m,

                },

        }


    except Exception as e:

        print(
            f"{symbol} ANALIZ HATASI:",
            e
        )

        return None


# ============================================================
# CANDIDATE FILTER
# ============================================================

def filter_candidates(
    candidates
):

    result = []

    for candidate in candidates:

        if not candidate:
            continue

        if (
            candidate["score"]
            < MIN_CANDIDATE_SCORE
        ):

            continue

        result.append(
            candidate
        )


    result.sort(

        key=lambda x:
        (
            x["score"],
            x["volume_ratio"],
            abs(x["momentum"]),

        ),

        reverse=True

    )

    return result[
        :MAX_RESULTS
    ]


# ============================================================
# STRATEGY ANALYSIS
# ============================================================

def run_strategies(
    candidate,
    btc_regime="NEUTRAL"
):

    """
    Adayı gerçek strateji motorlarına gönderir.

    Futures
    Spot
    Scalping
    """

    symbol = candidate[
        "symbol"
    ]

    data = candidate[
        "data"
    ]

    indicators = candidate[
        "indicators"
    ]

    structures = candidate[
        "structures"
    ]


    # --------------------------------------------------------
    # FUTURES
    # --------------------------------------------------------

    futures_result = {

        "signal":
            "UNAVAILABLE",

        "score":
            0,

    }


    if analyze_futures:

        try:

            futures_result = (
                analyze_futures(

                    symbol,

                    data,

                    indicators,

                    structures,

                    btc_regime,

                )
            )

        except Exception as e:

            futures_result = {

                "signal":
                    "ERROR",

                "score":
                    0,

                "reason":
                    str(e),

            }


    # --------------------------------------------------------
    # SPOT
    # --------------------------------------------------------

    spot_result = {

        "signal":
            "UNAVAILABLE",

        "score":
            0,

    }


    if analyze_spot:

        try:

            spot_result = (
                analyze_spot(

                    symbol,

                    data,

                    indicators,

                    structures,

                    btc_regime,

                )
            )

        except Exception as e:

            spot_result = {

                "signal":
                    "ERROR",

                "score":
                    0,

                "reason":
                    str(e),

            }


    # --------------------------------------------------------
    # SCALPING
    # --------------------------------------------------------

    scalping_result = {

        "signal":
            "UNAVAILABLE",

        "score":
            0,

    }


    # Scanner şu anda 1M indirmedi.
    # Bu yüzden scalping'i burada çalıştırmak
    # için 5M / 1M verisi ayrıca alınır.

    if analyze_scalping:

        try:

            if get_spot_klines:

                candles_5m = (
                    get_spot_klines(
                        symbol,
                        "5m",
                        300
                    )
                )

                candles_1m = (
                    get_spot_klines(
                        symbol,
                        "1m",
                        300
                    )
                )

                if (
                    candles_5m
                    and candles_1m
                ):

                    data_full = dict(
                        data
                    )

                    data_full[
                        "5m"
                    ] = candles_5m

                    data_full[
                        "1m"
                    ] = candles_1m


                    structures_full = dict(
                        structures
                    )

                    structures_full[
                        "5m"
                    ] = analyze_structure(
                        candles_5m
                    )

                    structures_full[
                        "1m"
                    ] = analyze_structure(
                        candles_1m
                    )


                    indicators_full = dict(
                        indicators
                    )

                    indicators_full[
                        "5m"
                    ] = calculate_indicators(
                        candles_5m
                    )

                    indicators_full[
                        "1m"
                    ] = calculate_indicators(
                        candles_1m
                    )


                    scalping_result = (
                        analyze_scalping(

                            symbol,

                            data_full[
                                "15m"
                            ],

                            candles_5m,

                            candles_1m,

                            structures_full[
                                "15m"
                            ],

                            structures_full[
                                "5m"
                            ],

                            structures_full[
                                "1m"
                            ],

                            indicators_full[
                                "15m"
                            ],

                            indicators_full[
                                "5m"
                            ],

                            indicators_full[
                                "1m"
                            ],

                            indicators_full[
                                "1m"
                            ].get(
                                "atr"
                            ),

                        )
                    )

        except Exception as e:

            scalping_result = {

                "signal":
                    "ERROR",

                "score":
                    0,

                "reason":
                    str(e),

            }


    return {

        "symbol":
            symbol,

        "candidate":
            candidate,

        "futures":
            futures_result,

        "spot":
            spot_result,

        "scalping":
            scalping_result,

    }


# ============================================================
# FINAL OPPORTUNITY RANKING
# ============================================================

def rank_opportunities(
    results
):

    opportunities = []


    for result in results:

        if not result:
            continue


        candidate = result.get(
            "candidate",
            {}
        )

        candidate_score = safe_float(
            candidate.get(
                "score"
            )
        )


        # ----------------------------------------------------
        # STRATEGY RESULTS
        # ----------------------------------------------------

        for strategy_name in (
            "futures",
            "spot",
            "scalping"
        ):

            strategy = result.get(
                strategy_name,
                {}
            )

            signal = strategy.get(
                "signal"
            )

            if signal not in (
                "LONG",
                "SHORT"
            ):

                continue


            strategy_score = safe_float(
                strategy.get(
                    "score"
                )
            )

            confidence = safe_float(
                strategy.get(
                    "confidence"
                )
            )


            # ------------------------------------------------
            # TOTAL QUALITY
            # ------------------------------------------------

            quality = (

                candidate_score
                + strategy_score
                + confidence / 20

            )


            opportunities.append({

                "symbol":
                    result["symbol"],

                "strategy":
                    strategy_name.upper(),

                "signal":
                    signal,

                "candidate_score":
                    candidate_score,

                "strategy_score":
                    strategy_score,

                "confidence":
                    confidence,

                "quality":
                    quality,

                "result":
                    strategy,

            })


    opportunities.sort(

        key=lambda x:
        (
            x["quality"],
            x["strategy_score"],
            x["confidence"],

        ),

        reverse=True

    )


    return opportunities[
        :MAX_RESULTS
    ]


# ============================================================
# MAIN SCANNER
# ============================================================

def scan_new_opportunities(
    btc_regime="NEUTRAL"
):

    """
    Yeni coinleri bulur ve strateji motorlarına gönderir.
    """

    print()
    print("=" * 70)

    print(
        "NEW COIN OPPORTUNITY SCANNER"
    )

    print("=" * 70)


    # --------------------------------------------------------
    # DISCOVERY
    # --------------------------------------------------------

    symbols = (
        discover_candidates()
    )


    print()

    print(
        f"Keşfedilen aday: "
        f"{len(symbols)}"
    )


    if not symbols:

        print(
            "Yeni coin bulunamadı."
        )

        return []


    # --------------------------------------------------------
    # FIRST PASS
    # --------------------------------------------------------

    candidates = []


    for symbol in symbols:

        print(
            f"Taranıyor: {symbol}"
        )

        candidate = (
            analyze_candidate(
                symbol
            )
        )

        if candidate:

            candidates.append(
                candidate
            )


    # --------------------------------------------------------
    # FILTER
    # --------------------------------------------------------

    candidates = filter_candidates(
        candidates
    )


    print()

    print(
        f"Kaliteli aday: "
        f"{len(candidates)}"
    )


    # --------------------------------------------------------
    # STRATEGIES
    # --------------------------------------------------------

    results = []


    for candidate in candidates:

        try:

            result = run_strategies(

                candidate,

                btc_regime,

            )

            results.append(
                result
            )

        except Exception as e:

            print(
                f'{candidate["symbol"]} '
                f'STRATEGY HATASI:',
                e
            )


    # --------------------------------------------------------
    # RANK
    # --------------------------------------------------------

    opportunities = (
        rank_opportunities(
            results
        )
    )


    return opportunities


# ============================================================
# REPORT
# ============================================================

def print_scanner_report(
    opportunities
):

    print()

    print("=" * 70)

    print(
        "NEW OPPORTUNITIES"
    )

    print("=" * 70)


    if not opportunities:

        print()

        print(
            "Şu anda yeterli kaliteye "
            "sahip yeni coin fırsatı yok."
        )

        print(
            "Bu normaldir; scanner zorla "
            "işlem üretmez."
        )

        return


    print()


    for index, opportunity in enumerate(

        opportunities,

        1

    ):

        print(

            f"{index}. "
            f"{opportunity['symbol']} | "
            f"{opportunity['strategy']} | "
            f"{opportunity['signal']} | "
            f"Score: "
            f"{opportunity['strategy_score']} | "
            f"Confidence: "
            f"%{opportunity['confidence']:.0f}"

        )


        result = opportunity[
            "result"
        ]


        if result.get(
            "entry"
        ) is not None:

            print(

                f"   Entry: "
                f"{result.get('entry')}"

            )


        if result.get(
            "stop"
        ) is not None:

            print(

                f"   SL: "
                f"{result.get('stop')}"

            )


        if result.get(
            "tp1"
        ) is not None:

            print(

                f"   TP1: "
                f"{result.get('tp1')}"

            )


        if result.get(
            "tp2"
        ) is not None:

            print(

                f"   TP2: "
                f"{result.get('tp2')}"

            )


        if result.get(
            "rr"
        ) is not None:

            print(

                f"   R/R: "
                f"{result.get('rr')}"

            )


        print()


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 70)

    print(
        "OPPORTUNITY SCANNER"
    )

    print("=" * 70)

    print()

    print(
        "Ana coinler:"
    )

    print(
        ", ".join(
            CORE_SYMBOLS
        )
    )

    print()

    print(
        "Yeni coin discovery:"
        " AKTİF"
    )

    print(
        "Futures:"
        " AKTİF"
    )

    print(
        "Spot:"
        " AKTİF"
    )

    print(
        "Scalping:"
        " 15M > 5M > 1M"
    )

    print()

    print(
        "Gerçek emir:"
        " KAPALI"
    )

    print()

    print(
        "Scanner hazır."
    )

    print("=" * 70)
