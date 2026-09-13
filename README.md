# crypto-research-agent
Free AI crypto research agent

## Early breakout scanner

The scanner is analysis-only. It does **not** place orders, connect to private trading accounts, or execute trades.

Pipeline:

- 4H: directional trend
- 1H: market structure / setup
- 15M: trigger conditions
- liquidity sweep, FVG, BOS/CHoCH, volume expansion, RSI and ATR
- 0-100 opportunity score and confidence
- trigger, invalidation/stop and 2R/3R reference targets

Run:

```bash
pip install -r requirements-scanner.txt
PYTHONPATH=. python early_scanner.py --limit 10 --min-volume 10000000
```

The output is informational. The user decides whether to enter a trade.
