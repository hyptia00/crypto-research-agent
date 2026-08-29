# ============================================================
# CRYPTO RESEARCH AGENT
# MAIN AGENT
# ============================================================

from config import (
    CORE_COINS,
    DISCOVERY_ENABLED,
    MIN_24H_VOLUME_USDT,
)

from market.data_engine import (
    get_multi_timeframe_data,
    discover_usdt_markets,
    get_price,
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

from strategies.scanner import (
    scan_market,
    print_scanner_report,
)

from engine.aggregator import (
    aggregate,
)

from engine.risk import (
    apply_risk,
    risk_rejection_reason,
)

from engine.paper import (
    PaperTradingEngine,
)


# ============================================================
# SETTINGS
# ============================================================

PAPER_BALANCE = 1000.0

DISCOVERY_LIMIT = 10

DATA_LIMIT = 200

MAX_SIGNALS_PER_RUN = 10


# ============================================================
# PRINT
# ============================================================

def print_header():

    print()
    print("=" * 80)
    print(
        "CRYPTO RESEARCH AGENT"
    )
    print(
        "MULTI STRATEGY / PAPER TRADING"
    )
    print("=" * 80)


# ============================================================
# SIGNAL REPORT
# ============================================================

def print_signal(
    signal
):

    if not signal:
        return

    print()
    print("-" * 80)

    print(
        f"SYMBOL      : "
        f"{signal.get('symbol')}"
    )

    print(
        f"MARKET      : "
        f"{signal.get('market')}"
    )

    print(
        f"SIDE        : "
        f"{signal.get('side')}"
    )

    print(
        f"ENTRY       : "
        f"{signal.get('entry', 0):.8f}"
    )

    print(
        f"STOP        : "
        f"{signal.get('stop', 0):.8f}"
    )

    print(
        f"TP1         : "
        f"{signal.get('tp1', 0):.8f}"
    )

    print(
        f"TP2         : "
        f"{signal.get('tp2', 0):.8f}"
    )

    print(
        f"R/R         : "
        f"{signal.get('rr', 0):.2f}"
    )

    print(
        f"SCORE       : "
        f"{signal.get('score', 0)}"
    )

    print(
        f"CONFIDENCE  : "
        f"{signal.get('confidence', 0):.1f}%"
    )

    print(
        f"STATUS      : "
        f"{signal.get('status', 'N/A')}"
    )

    if "risk_status" in signal:

        print(
            f"RISK        : "
            f"{signal.get('risk_status')}"
        )

        print(
            f"RISK %      : "
            f"{signal.get('risk_percent', 0):.2f}%"
        )

        print(
            f"POSITION    : "
            f"{signal.get('position_percent', 0):.2f}%"
        )

        print(
            f"QUANTITY    : "
            f"{signal.get('quantity', 0):.8f}"
        )

    reasons = signal.get(
        "reasons",
        []
    )

    if reasons:

        print()
        print("REASONS:")

        for reason in reasons:

            print(
                f"  + {reason}"
            )

    print("-" * 80)


# ============================================================
# ANALYZE SYMBOL
# ============================================================

def analyze_symbol(
    symbol,
    paper_engine,
):
    """
    Tek coin için:

        Data
         ↓
        Futures
         ↓
        Spot
         ↓
        Scalping
         ↓
        Aggregator
         ↓
        Risk
         ↓
        Paper

    """

    print()
    print(
        f"[ANALYZE] {symbol}"
    )

    # ========================================================
    # DATA
    # ========================================================

    try:

        data = get_multi_timeframe_data(

            symbol,

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
            f"DATA ERROR: {exc}"
        )

        return None

    if not data:
        return None

    # ========================================================
    # FUTURES
    # ========================================================

    try:

        futures_signal = analyze_futures(
            symbol,
            data
        )

    except Exception as exc:

        print(
            f"FUTURES ERROR: {exc}"
        )

        futures_signal = None

    # ========================================================
    # SPOT
    # ========================================================

    try:

        spot_signal = analyze_spot(
            symbol,
            data
        )

    except Exception as exc:

        print(
            f"SPOT ERROR: {exc}"
        )

        spot_signal = None

    # ========================================================
    # SCALPING
    # ========================================================

    try:

        scalping_signal = analyze_scalping(
            symbol,
            data
        )

    except Exception as exc:

        print(
            f"SCALPING ERROR: {exc}"
        )

        scalping_signal = None

    # ========================================================
    # PRINT RAW SIGNALS
    # ========================================================

    raw_signals = []

    if futures_signal:
        raw_signals.append(
            futures_signal
        )

    if spot_signal:
        raw_signals.append(
            spot_signal
        )

    if scalping_signal:
        raw_signals.append(
            scalping_signal
        )

    for signal in raw_signals:

        if signal.get(
            "side"
        ) != "WAIT":

            print_signal(
                signal
            )

    # ========================================================
    # AGGREGATOR
    # ========================================================

    try:

        aggregated = aggregate(
            raw_signals
        )

    except Exception as exc:

        print(
            f"AGGREGATOR ERROR: {exc}"
        )

        return None

    if not aggregated:

        print(
            f"[{symbol}] "
            f"No qualified consensus."
        )

        return None

    if aggregated.get(
        "side"
    ) == "WAIT":

        print(
            f"[{symbol}] "
            f"Aggregator: WAIT"
        )

        return None

    print()
    print(
        f"[{symbol}] "
        f"AGGREGATED SIGNAL"
    )

    print_signal(
        aggregated
    )

    # ========================================================
    # RISK
    # ========================================================

    approved = apply_risk(
        aggregated,
        PAPER_BALANCE
    )

    if not approved:

        reason = risk_rejection_reason(
            aggregated
        )

        print(
            f"[{symbol}] "
            f"RISK REJECTED: "
            f"{reason}"
        )

        return None

    # ========================================================
    # APPROVED
    # ========================================================

    print()
    print(
        f"[{symbol}] "
        f"RISK APPROVED"
    )

    print_signal(
        approved
    )

    # ========================================================
    # PAPER POSITION
    # ========================================================

    position = (
        paper_engine.open_position(
            approved
        )
    )

    if position:

        print()
        print(
            f"[PAPER OPEN] "
            f"{symbol} "
            f"{position['side']} "
            f"@ "
            f"{position['entry']}"
        )

    else:

        print(
            f"[PAPER] "
            f"Position not opened "
            f"(duplicate/max positions)"
        )

    return approved


# ============================================================
# DISCOVERY
# ============================================================

def discover_symbols():

    if not DISCOVERY_ENABLED:

        return []

    try:

        candidates = scan_market(
            limit=DISCOVERY_LIMIT
        )

        print_scanner_report(
            candidates
        )

        return [
            x["symbol"]
            for x in candidates
            if x.get("symbol")
        ]

    except Exception as exc:

        print(
            f"DISCOVERY ERROR: {exc}"
        )

        return []


# ============================================================
# BUILD SYMBOL LIST
# ============================================================

def build_symbol_list():

    symbols = list(
        CORE_COINS
    )

    discovered = (
        discover_symbols()
    )

    for symbol in discovered:

        if symbol not in symbols:

            symbols.append(
                symbol
            )

    return symbols


# ============================================================
# UPDATE PAPER PRICES
# ============================================================

def update_paper_positions(
    paper_engine
):

    positions = (
        paper_engine
        .get_open_positions()
    )

    if not positions:
        return

    prices = {}

    for position in positions:

        symbol = position[
            "symbol"
        ]

        try:

            prices[symbol] = (
                get_price(
                    symbol
                )
            )

        except Exception as exc:

            print(
                f"PRICE ERROR "
                f"{symbol}: "
                f"{exc}"
            )

    if not prices:
        return

    events = (
        paper_engine.update_all(
            prices
        )
    )

    for event in events:

        print(
            f"[PAPER EVENT] "
            f"{event}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print_header()

    # ========================================================
    # PAPER ENGINE
    # ========================================================

    paper_engine = (
        PaperTradingEngine(
            PAPER_BALANCE
        )
    )

    # ========================================================
    # SYMBOLS
    # ========================================================

    symbols = (
        build_symbol_list()
    )

    print()
    print(
        f"Total symbols: "
        f"{len(symbols)}"
    )

    print(
        f"Core coins: "
        f"{len(CORE_COINS)}"
    )

    # ========================================================
    # ANALYSIS
    # ========================================================

    approved_signals = []

    for symbol in symbols:

        try:

            signal = analyze_symbol(

                symbol,

                paper_engine

            )

            if signal:

                approved_signals.append(
                    signal
                )

        except Exception as exc:

            print(
                f"MAIN ERROR "
                f"{symbol}: "
                f"{exc}"
            )

    # ========================================================
    # LIMIT SIGNALS
    # ========================================================

    approved_signals.sort(

        key=lambda x: (

            x.get(
                "confidence",
                0
            ),

            x.get(
                "score",
                0
            ),

        ),

        reverse=True,

    )

    approved_signals = (
        approved_signals[
            :MAX_SIGNALS_PER_RUN
        ]
    )

    # ========================================================
    # UPDATE POSITIONS
    # ========================================================

    update_paper_positions(
        paper_engine
    )

    # ========================================================
    # FINAL REPORT
    # ========================================================

    print()
    print("=" * 80)
    print(
        "FINAL SIGNAL SUMMARY"
    )
    print("=" * 80)

    if not approved_signals:

        print(
            "Bu taramada onaylanmış "
            "işlem bulunamadı."
        )

    else:

        for signal in (
            approved_signals
        ):

            print(
                f"{signal.get('symbol')} | "
                f"{signal.get('side')} | "
                f"Confidence="
                f"{signal.get('confidence', 0):.1f}% | "
                f"Score="
                f"{signal.get('score', 0)} | "
                f"Entry="
                f"{signal.get('entry', 0):.8f}"
            )

    # ========================================================
    # PAPER REPORT
    # ========================================================

    paper_engine.report()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()
