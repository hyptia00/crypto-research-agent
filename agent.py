# ============================================================
# CRYPTO TRADING AGENT
# MAIN ORCHESTRATOR
# ============================================================

from config import (
    CORE_COINS,
    DISCOVERY_ENABLED,
    DISCOVERY_LIMIT,
    MIN_DISCOVERY_VOLUME,
    DATA_LIMIT,

    FUTURES_ENABLED,
    SPOT_ENABLED,
    SCALPING_ENABLED,

    STARTING_BALANCE,
    RISK_PER_TRADE,
    MAX_OPEN_POSITIONS,

    MIN_AGGREGATED_SCORE,
    MIN_AGGREGATED_CONFIDENCE,
)

from market.data_engine import (
    get_multi_timeframe_data,
    get_usdt_tickers,
)

from strategies.scanner import (
    scan_market,
    print_scanner_report,
)

from strategies.futures import (
    analyze_futures,
)

from strategies.spot import (
    analyze_spot,
)

from strategies.scalping import (
    analyze_scalping,
)

from engine.aggregator import (
    aggregate_signals,
)

from engine.risk import (
    get_final_signal,
)

from engine.paper import (
    PaperTrader,
)


# ============================================================
# SETTINGS
# ============================================================

MAX_SIGNALS = 10

TIMEFRAMES = [
    "4h",
    "1h",
    "15m",
    "5m",
    "1m",
]


# ============================================================
# CORE COINS
# ============================================================

def normalize_core_coins():

    result = []

    for coin in CORE_COINS:

        symbol = str(
            coin
        ).upper().strip()

        if not symbol:
            continue

        if not symbol.endswith("USDT"):
            symbol += "USDT"

        if symbol not in result:
            result.append(symbol)

    return result


# ============================================================
# DISCOVERY
# ============================================================

def discover_symbols():

    core = normalize_core_coins()

    symbols = list(core)

    if not DISCOVERY_ENABLED:
        return symbols

    try:

        tickers = get_usdt_tickers()

        candidates = scan_market(
            tickers=tickers,
            core_coins=core,
            min_volume=MIN_DISCOVERY_VOLUME,
            limit=DISCOVERY_LIMIT,
        )

        print_scanner_report(
            candidates
        )

        for candidate in candidates:

            symbol = str(
                candidate.get(
                    "symbol",
                    ""
                )
            ).upper().strip()

            if not symbol:
                continue

            if not symbol.endswith("USDT"):
                continue

            if symbol not in symbols:
                symbols.append(symbol)

    except Exception as exc:

        print(
            f"[DISCOVERY ERROR] {exc}"
        )

    return symbols


# ============================================================
# DATA
# ============================================================

def load_data(symbol):

    symbol = str(
        symbol
    ).upper().strip()

    if not symbol:
        return {}

    try:

        data = get_multi_timeframe_data(
            symbol=symbol,
            timeframes=TIMEFRAMES,
            limit=DATA_LIMIT,
        )

        if not isinstance(
            data,
            dict
        ):
            return {}

        valid_data = {}

        for timeframe in TIMEFRAMES:

            df = data.get(
                timeframe
            )

            if df is None:
                continue

            if getattr(
                df,
                "empty",
                True,
            ):
                continue

            valid_data[
                timeframe
            ] = df

        return valid_data

    except Exception as exc:

        print(
            f"[DATA ERROR] "
            f"{symbol}: {exc}"
        )

        return {}


# ============================================================
# BTC REGIME
# ============================================================

def calculate_btc_regime(
    data
):

    if not isinstance(
        data,
        dict
    ):
        return "UNKNOWN"

    df = data.get(
        "1h"
    )

    if df is None:
        return "UNKNOWN"

    if getattr(
        df,
        "empty",
        True,
    ):
        return "UNKNOWN"

    if "close" not in df.columns:
        return "UNKNOWN"

    if len(df) < 50:
        return "UNKNOWN"

    try:

        close = float(
            df["close"].iloc[-1]
        )

        ema20 = (
            df["close"]
            .ewm(
                span=20,
                adjust=False,
            )
            .mean()
            .iloc[-1]
        )

        ema50 = (
            df["close"]
            .ewm(
                span=50,
                adjust=False,
            )
            .mean()
            .iloc[-1]
        )

        if close > ema20 > ema50:
            return "LONG"

        if close < ema20 < ema50:
            return "SHORT"

        return "NEUTRAL"

    except Exception as exc:

        print(
            f"[BTC REGIME ERROR] "
            f"{exc}"
        )

        return "UNKNOWN"


# ============================================================
# ANALYZE ONE SYMBOL
# ============================================================

def analyze_symbol(
    symbol,
    btc_regime,
    data=None,
):

    symbol = str(
        symbol
    ).upper().strip()

    print()
    print(
        f"[ANALYZE] {symbol}"
    )

    if data is None:
        data = load_data(
            symbol
        )

    if not data:
        print(
            f"[SKIP] "
            f"{symbol}: NO DATA"
        )
        return []

    signals = []

    # ========================================================
    # FUTURES
    # ========================================================

    if FUTURES_ENABLED:

        try:

            df_1h = data.get(
                "1h"
            )

            if (
                df_1h is not None
                and not df_1h.empty
            ):

                signal = analyze_futures(
                    df=df_1h,
                    symbol=symbol,
                    btc_regime=btc_regime,
                )

                if (
                    isinstance(
                        signal,
                        dict,
                    )
                    and signal.get(
                        "direction"
                    ) != "WAIT"
                ):

                    signals.append(
                        signal
                    )

        except Exception as exc:

            print(
                f"[FUTURES ERROR] "
                f"{symbol}: {exc}"
            )

    # ========================================================
    # SPOT
    # ========================================================

    if SPOT_ENABLED:

        try:

            df_4h = data.get(
                "4h"
            )

            if (
                df_4h is not None
                and not df_4h.empty
            ):

                signal = analyze_spot(
                    df=df_4h,
                    symbol=symbol,
                    btc_regime=btc_regime,
                )

                if (
                    isinstance(
                        signal,
                        dict,
                    )
                    and signal.get(
                        "direction"
                    ) != "WAIT"
                ):

                    signals.append(
                        signal
                    )

        except Exception as exc:

            print(
                f"[SPOT ERROR] "
                f"{symbol}: {exc}"
            )

    # ========================================================
    # SCALPING
    # ========================================================

    if SCALPING_ENABLED:

        try:

            signal = analyze_scalping(
                data=data,
                symbol=symbol,
                btc_regime=btc_regime,
            )

            if (
                isinstance(
                    signal,
                    dict,
                )
                and signal.get(
                    "direction"
                ) != "WAIT"
            ):

                signals.append(
                    signal
                )

        except Exception as exc:

            print(
                f"[SCALPING ERROR] "
                f"{symbol}: {exc}"
            )

    return signals


# ============================================================
# SIGNAL SUMMARY
# ============================================================

def print_signal(
    signal
):

    print()
    print(
        "-" * 70
    )

    print(
        f"SYMBOL      : "
        f"{signal.get('symbol')}"
    )

    print(
        f"STRATEGY    : "
        f"{signal.get('strategy')}"
    )

    print(
        f"DIRECTION   : "
        f"{signal.get('direction')}"
    )

    print(
        f"ENTRY       : "
        f"{signal.get('entry')}"
    )

    print(
        f"STOP        : "
        f"{signal.get('stop')}"
    )

    print(
        f"TP1         : "
        f"{signal.get('tp1')}"
    )

    print(
        f"TP2         : "
        f"{signal.get('tp2')}"
    )

    print(
        f"R/R         : "
        f"{signal.get('rr')}"
    )

    print(
        f"SCORE       : "
        f"{signal.get('score')}"
    )

    print(
        f"CONFIDENCE  : "
        f"{signal.get('confidence')}%"
    )

    print(
        f"MSB         : "
        f"{signal.get('msb', False)}"
    )

    print(
        f"CHoCH       : "
        f"{signal.get('choch', False)}"
    )

    print(
        f"SWEEP       : "
        f"{signal.get('liquidity_sweep', False)}"
    )

    print(
        f"FVG         : "
        f"{bool(signal.get('fvg'))}"
    )

    print(
        "-" * 70
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print(
        "=" * 80
    )

    print(
        "CRYPTO TRADING AGENT"
    )

    print(
        "FUTURES + SPOT + SCALPING"
    )

    print(
        "=" * 80
    )

    # ========================================================
    # PAPER TRADER
    # ========================================================

    paper = PaperTrader(
        STARTING_BALANCE
    )

    # ========================================================
    # LOAD BTC ONCE
    # ========================================================

    btc_data = load_data(
        "BTCUSDT"
    )

    btc_regime = calculate_btc_regime(
        btc_data
    )

    print()
    print(
        f"BTC REGIME: "
        f"{btc_regime}"
    )

    # ========================================================
    # SYMBOL DISCOVERY
    # ========================================================

    symbols = discover_symbols()

    print()
    print(
        f"SYMBOLS: "
        f"{len(symbols)}"
    )

    # ========================================================
    # COLLECT SIGNALS
    # ========================================================

    all_signals = []

    for symbol in symbols:

        try:

            # BTC verisini tekrar çekme.
            if symbol == "BTCUSDT":

                data = btc_data

            else:

                data = load_data(
                    symbol
                )

            signals = analyze_symbol(
                symbol=symbol,
                btc_regime=btc_regime,
                data=data,
            )

            for signal in signals:

                if not isinstance(
                    signal,
                    dict,
                ):
                    continue

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

                all_signals.append(
                    signal
                )

        except Exception as exc:

            print(
                f"[ERROR] "
                f"{symbol}: {exc}"
            )

    # ========================================================
    # AGGREGATION
    # ========================================================

    aggregated = aggregate_signals(
        all_signals,
        min_score=MIN_AGGREGATED_SCORE,
        min_confidence=MIN_AGGREGATED_CONFIDENCE,
    )

    # ========================================================
    # RISK FILTER
    # ========================================================

    final_signals = []

    for signal in aggregated:

        if not isinstance(
            signal,
            dict,
        ):
            continue

        result = get_final_signal(
            [signal],
            btc_regime=btc_regime,
            min_confidence=MIN_AGGREGATED_CONFIDENCE,
            min_rr=1.8,
        )

        if result is None:
            continue

        result["execution_ready"] = True

        final_signals.append(
            result
        )

    # ========================================================
    # RANK
    # ========================================================

    def ranking(signal):

        try:
            confidence = float(
                signal.get(
                    "confidence",
                    0,
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            confidence = 0.0

        try:
            score = float(
                signal.get(
                    "score",
                    0,
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            score = 0.0

        try:
            rr = float(
                signal.get(
                    "rr",
                    0,
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            rr = 0.0

        return (
            confidence * 0.50
            +
            score * 4.0
            +
            min(rr, 4.0) * 5.0
        )

    final_signals.sort(
        key=ranking,
        reverse=True,
    )

    final_signals = final_signals[
        :MAX_SIGNALS
    ]

    # ========================================================
    # FINAL SIGNALS
    # ========================================================

    print()
    print(
        "=" * 80
    )

    print(
        "FINAL SIGNALS"
    )

    print(
        "=" * 80
    )

    if not final_signals:

        print(
            "No qualified signals."
        )

    # ========================================================
    # PAPER EXECUTION
    # ========================================================

    for signal in final_signals:

        print_signal(
            signal
        )

        # ----------------------------------------------------
        # MAX OPEN POSITION CHECK
        # ----------------------------------------------------

        status = paper.status()

        open_positions = status.get(
            "open_positions",
            {}
        )

        if len(open_positions) >= MAX_OPEN_POSITIONS:

            print(
                "PAPER: "
                "SKIPPED - "
                "MAX OPEN POSITIONS"
            )

            continue

        # ----------------------------------------------------
        # DUPLICATE POSITION CHECK
        # ----------------------------------------------------

        symbol = str(
            signal.get(
                "symbol",
                "",
            )
        ).upper()

        if symbol in open_positions:

            print(
                "PAPER: "
                "SKIPPED - "
                "POSITION ALREADY EXISTS"
            )

            continue

        # ----------------------------------------------------
        # RISK AMOUNT
        # ----------------------------------------------------

        risk_amount = (
            paper.balance
            *
            float(RISK_PER_TRADE)
        )

        if risk_amount <= 0:

            print(
                "PAPER: "
                "SKIPPED - "
                "INVALID RISK"
            )

            continue

        # ----------------------------------------------------
        # PAPER ENTRY
        # ----------------------------------------------------

        result = paper.open_position(

            symbol=symbol,

            side=signal[
                "direction"
            ],

            entry=signal[
                "entry"
            ],

            stop=signal[
                "stop"
            ],

            tp1=signal[
                "tp1"
            ],

            tp2=signal[
                "tp2"
            ],

            risk_amount=risk_amount,
        )

        print(
            f"PAPER: "
            f"{result}"
        )

    # ========================================================
    # PAPER STATUS
    # ========================================================

    print()
    print(
        "=" * 80
    )

    print(
        "PAPER ACCOUNT"
    )

    print(
        "=" * 80
    )

    print(
        paper.status()
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()
