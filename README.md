# crypto-research-agent / Lilith Trading Intelligence

Analysis-only crypto intelligence system. **No order placement, no private trading-account connection, no execution code.**

## Architecture

```text
Market Data Layer
  Binance / Bybit / OKX
  OHLCV | OI | CVD | Funding | Liquidations | Orderbook
          ↓
Event Intelligence Layer
  Agent-Reach + RSS/web sources
  News | social/web search | GitHub | YouTube-capable upstream tools
          ↓
Analysis Engine
  4H → 1H → 15M → 5M → 1M
  trend | BOS/CHoCH | liquidity sweep | FVG | volume | RSI | ATR
  OI/CVD divergence | orderbook imbalance | event context
          ↓
Alert Engine
  early movement | OI anomaly | CVD anomaly | liquidation cluster
  news catalyst | event/social anomaly | multi-factor setup
          ↓
Human Decision
  evidence + scenario + invalidation + reference targets
```

## What is implemented

- Normalized REST adapters for Binance Futures, Bybit Linear and OKX SWAP.
- Public OHLCV, open interest, funding, trades, orderbook and Binance force-order data.
- Rolling CVD from public trade/tape data and persisted OI/CVD state in SQLite.
- Cross-exchange aggregation with partial-data tolerance.
- Deterministic multi-timeframe technical analysis.
- Agent-Reach health check and optional Exa/RSS event-intelligence layer. Agent-Reach is used as the internet capability router; its upstream tools remain responsible for actual platform reads/searches.
- Early-warning alerts and persistent analysis history.
- Unit tests, compile check and a public-exchange live smoke test in GitHub Actions.

## Run

```bash
pip install -r requirements-system.txt
PYTHONPATH=. python lilith.py doctor
PYTHONPATH=. python lilith.py scan --symbols BTCUSDT,ETHUSDT
PYTHONPATH=. python lilith.py run
```

Configuration is environment based:

```bash
export LILITH_SYMBOLS=BTCUSDT,ETHUSDT
export LILITH_EXCHANGES=binance,bybit,okx
export LILITH_INTERVAL=30
export LILITH_DB=data/lilith.db
```

For Agent-Reach-backed event search, install/configure Agent-Reach and its upstream tools on the host, then verify with:

```bash
agent-reach doctor --json
```

The system degrades gracefully when Agent-Reach or a particular exchange is unavailable; it does not fabricate missing OI/CVD/news confirmation.

## Existing early-breakout scanner

The original scanner remains available:

```bash
pip install -r requirements-scanner.txt
PYTHONPATH=. python early_scanner.py --limit 10 --min-volume 10000000
```

The existing scanner was also hardened against the pandas RSI `NAType` failure discovered by CI.

## Verification

CI runs:

1. Python compilation.
2. Full pytest suite.
3. Public live smoke test against Binance, Bybit and OKX.

The live smoke test currently confirms that at least one public exchange endpoint is reachable; CI observed OKX successfully returning BTCUSDT price, OI and funding while Binance/Bybit were region/HTTP restricted in that runner.

The user remains the sole decision-maker for any trade. This repository contains no automatic execution path.
