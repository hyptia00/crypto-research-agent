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
    FUTURES_MIN_SCORE,
    FUTURES_MIN_CONFIDENCE,
    FUTURES_MIN_RR,
    SPOT_MIN_SCORE,
    SPOT_MIN_CONFIDENCE,
    SPOT_MIN_RR,
    SCALPING_MIN_SCORE,
    SCALPING_MIN_CONFIDENCE,
    SCALPING_MIN_RR,
    STARTING_BALANCE,
    RISK_PER_TRADE,
    MAX_OPEN_POSITIONS,
    MIN_AGGREGATED_SCORE,
    MIN_AGGREGATED_CONFIDENCE,
)

from market.data_engine import (
    get_multi_timeframe_data,
    get_price,
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


# ============================================================
# CORE COINS
# ============================================================

def normalize_core_coins():

    result = []

    for coin in CORE_COINS:

        symbol = str(
            coin
        ).upper()

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
            limit=DISCOVERY_LIMIT,
        )

        print_scanner_report(
            candidates
        )

        for candidate in candidates:

            symbol = candidate.get(
                "symbol"
            )

            if (
                symbol
                and symbol not in symbols
            ):

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

    try:

        return get_multi_timeframe_data(
            symbol=symbol,
            timeframes=[
                "4h",
                "1h",
                "15m",
                "5m",
                "1m",
            ],
            limit=DATA_LIMIT,
        )

    except Exception as exc:

        print(
            f"[DATA ERROR] "
            f"{symbol}: {exc}"
        )

        return {}


# ============================================================
# BTC REGIME
# ============================================================

def get_btc_regime():

    try:

        data = load_data(
            "BTCUSDT"
        )

        df = data.get(
            "1h"
        )

        if df is None or len(df) < 50:
            return "UNKNOWN"

        close = float(
            df["close"].iloc[-1]
        )

        ema20 = (
            df["close"]
            .ewm(
                span=20,
                adjust=False
            )
            .mean()
            .iloc[-1]
        )

        ema50 = (
            df["close"]
            .ewm(
                span=50,
                adjust=False
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
):

    print()
    print(
        f"[ANALYZE] {symbol}"
    )

    data = load_data(
        symbol
    )

    if not data:
        return []

    signals = []

    # ========================================================
    # FUTURES
    # ========================================================

    try:

        df_1h = data.get(
            "1h"
        )

        if df_1h is not None:

            signal = analyze_futures(
                df=df_1h,
                symbol=symbol,
                btc_regime=btc_regime,
            )

            if signal:
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

    try:

        df_4h = data.get(
            "4h"
        )

        if df_4h is not None:

            signal = analyze_spot(
                df=df_4h,
                symbol=symbol,
                btc_regime=btc_regime,
            )

            if signal:
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

    try:

        signal = analyze_scalping(
            data=data,
            symbol=symbol,
            btc_regime=btc_regime,
        )

        if signal:
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
    print("=" * 80)
    print(
        "CRYPTO TRADING AGENT"
    )
    print(
        "FUTURES + SPOT + SCALPING"
    )
    print("=" * 80)

    # ========================================================
    # PAPER TRADER
    # ========================================================

    paper = PaperTrader(
        STARTING_BALANCE
    )

    # ========================================================
    # BTC REGIME
    # ========================================================

    btc_regime = get_btc_regime()

    print()
    print(
        f"BTC REGIME: "
        f"{btc_regime}"
    )

    # ========================================================
    # SYMBOLS
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

            signals = analyze_symbol(
                symbol,
                btc_regime,
            )

            for signal in signals:

                if signal.get(
                    "direction"
                ) != "WAIT":

                    all_signals.append(
                        signal
                    )

        except Exception as exc:

            print(
                f"[ERROR] "
                f"{symbol}: {exc}"
            )

    # ========================================================
    # AGGREGATE
    # ========================================================

    aggregated = aggregate_signals(
        all_signals,
        min_score=6,
        min_confidence=60,
    )

    # ========================================================
    # RISK FILTER
    # ========================================================

    final_signals = []

    for signal in aggregated:

        if signal.get(
            "direction"
        ) == "WAIT":

            continue

        result = get_final_signal(
            [signal],
            btc_regime=btc_regime,
            min_confidence=60,
            min_rr=1.8,
        )

        if result:

            final_signals.append(
                result
            )

    # ========================================================
    # RANK
    # ========================================================

    final_signals.sort(
        key=lambda x: (
            float(
                x.get(
                    "confidence",
                    0
                )
            ),
            float(
                x.get(
                    "rr",
                    0
                )
            ),
        ),
        reverse=True,
    )

    final_signals = (
        final_signals[
            :MAX_SIGNALS
        ]
    )

    # ========================================================
    # PRINT
    # ========================================================

    print()
    print("=" * 80)
    print(
        "FINAL SIGNALS"
    )
    print("=" * 80)

    if not final_signals:

        print(
            "No qualified signals."
        )

    for signal in final_signals:

        print_signal(
            signal
        )

        # ----------------------------------------------------
        # PAPER ENTRY
        # ----------------------------------------------------

        result = paper.open_position(
            symbol=signal["symbol"],
            side=signal["direction"],
            entry=signal["entry"],
            stop=signal["stop"],
            tp1=signal["tp1"],
            tp2=signal["tp2"],
            risk_amount=(
                paper.balance * 0.01
            ),
        )

        print(
            f"PAPER: "
            f"{result}"
        )

    # ========================================================
    # PAPER STATUS
    # ========================================================

    print()
    print("=" * 80)
    print(
        "PAPER ACCOUNT"
    )
    print("=" * 80)

    print(
        paper.status()
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
